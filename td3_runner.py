import argparse
import os
import json
import torch
import numpy as np
from td3 import TD3, ReplayBuffer
from circuit_env import CircuitEnv
from datetime import datetime
import shutil
from pathlib import Path

from utils import gen_utils 
from utils import file_utils 
from td3_llm import (
    collect_low_fidelity_elites,
    save_best_candidate_record,
    seed_replay_from_category_memory,
    seed_replay_from_low_fidelity_elites,
)
warmup_step = 1000
def readParser(argv=None):
    parser = argparse.ArgumentParser(description='TD3-based RL for Circuit Sizing')

    parser.add_argument('--seed', type=int, default=123456, metavar='N',
                        help='random seed (default: 123456)')

    parser.add_argument('--noise_sigma', type=float, default="0.1", # explore, if bad result or early stop, try larger, if vibration, try smaller
                        help='fixed noise sigma added to the deterministic action')

    parser.add_argument('--gamma', type=float, default=0.99, metavar='G',
                        help='discount factor for reward (default: 0.99)')
    
    parser.add_argument('--tau', type=float, default=0.005, metavar='G', #target network weights update
                        help='target smoothing coefficient(τ) (default: 0.005)')
    
    parser.add_argument('--target_update_interval', type=int, default=1, metavar='N',
                        help='Value target update per no. of updates per step (default: 1)')
    
    parser.add_argument('--actor_update_interval', type=int, default=2, metavar='N',
                        help='Actor target update per no. of updates per step (default: 2)')
    
    parser.add_argument('--hidden_size', type=int, default=256, metavar='N', # overfitting？
                        help='hidden size (default: 256)')
    
    parser.add_argument('--batch_size', type=int, default="256", metavar='N',# past experirence
                        help='hidden size')
    
    parser.add_argument('--w', type=int, default=f"{warmup_step}", metavar='N',
                        help='number of warmup steps')
    
    parser.add_argument('--T', type=int, default=5_000, metavar='N',
                        help='total training steps (default: 10_000)')
    
    parser.add_argument('--pi_lr', type=float, default="2e-4", metavar='G',
                        help='learning rate')
    
    parser.add_argument('--q_lr', type=float, default="2e-4", metavar='G',
                        help='learning rate')

    parser.add_argument('--replay_size', type=int, default=1000000, metavar='N',
                        help='size of replay buffer (default: 10000000)')

    parser.add_argument('--cuda', default=False, action="store_true",
                        help='run on CUDA (default: True)')
    
    parser.add_argument('--run_id', type=str, default=datetime.now().strftime('%Y-%m-%d--%H-%M-%S'), metavar='N',
                        help='run identifier (default: current time)')

    parser.add_argument('--circuit_name', type=str, default=None,
                        help='circuit YAML/netlist id to size when running td3_runner.py directly')

    parser.add_argument('--warm_start_category', type=str, default=None,
                        help='optional category-memory key for td3_llm warm-start')

    parser.add_argument('--warm_start_records', type=int, default=20,
                        help='maximum compatible category-memory records to evaluate before TD3')

    parser.add_argument('--warm_start_reduce_random', action="store_true",
                        help='subtract seeded records from random warmup count')

    parser.add_argument('--dc_seed_samples', type=int, default=0,
                        help='number of cheap OP/DC samples to rank before full TD3 warmup')

    parser.add_argument('--dc_seed_elites', type=int, default=0,
                        help='number of OP/DC elite candidates to evaluate with full specs and seed into replay')

    parser.add_argument('--dc_seed_method', type=str, default="random", choices=("random", "sobol"),
                        help='sampling method for OP/DC candidate generation')

    parser.add_argument('--low_fidelity_strategy', type=str, default="ac_gain",
                        choices=("ac_gain", "op_domain", "op_ac_domain"),
                        help='low-fidelity reward strategy for candidate generation')

    parser.add_argument('--full_warmup_steps', type=int, default=None,
                        help='override the number of random full-spec warmup steps after optional seeding')
    
    return parser.parse_args(argv)

def train(args, env, agent, env_pool):
    total_steps = warmup_exploration(args, env, env_pool, agent)
    while total_steps < args.T:
        obs = env.reset()
        done = False
        while not done:
            action = agent.select_action(obs)
            next_state, reward, done, info = env.step(action)
            # if done:
            #     print("is done? :",done)
            #     utils_agent.test_delay(30)
            env_pool.push(obs, action, reward, next_state, done)
            obs = next_state
            train_policy(args, env_pool, agent, total_steps)
            total_steps += 1
            print(f"==total_steps{total_steps}")
            # clean up the no_backup folder every 100 steps
            if total_steps % 100 == 0:
                file_utils.delete_all_files_except_dir("./no_backup/output_netlists/")
                # os.system('./clean.sh')

def warmup_exploration(args, env, env_pool, agent):
    step_counter = 0
    full_warmup_steps = getattr(args, "full_warmup_steps", None)
    target_random_warmup = args.w if full_warmup_steps is None else max(0, int(full_warmup_steps))
    seed_log_dir = Path(env.solutions_dir) / "warm_start"

    if getattr(args, "dc_seed_samples", 0) > 0 and getattr(args, "dc_seed_elites", 0) > 0:
        elites = collect_low_fidelity_elites(
            env,
            sample_count=args.dc_seed_samples,
            elite_count=args.dc_seed_elites,
            method=getattr(args, "dc_seed_method", "random"),
            seed=getattr(args, "seed", None),
            strategy=getattr(args, "low_fidelity_strategy", "ac_gain"),
            log_path=seed_log_dir / "op_dc_candidates.json",
        )
        seeded = seed_replay_from_low_fidelity_elites(
            env,
            env_pool,
            elites,
            log_path=seed_log_dir / "op_dc_seeded_transitions.json",
        )
        if getattr(args, "warm_start_reduce_random", False):
            step_counter = min(seeded, target_random_warmup)
            print(
                f"[td3_llm] Random warmup starts at {step_counter}/"
                f"{target_random_warmup} after OP/DC seeding."
            )

    if getattr(args, "warm_start_category", None):
        seeded = seed_replay_from_category_memory(
            env,
            env_pool,
            args.warm_start_category,
            max_records=getattr(args, "warm_start_records", 20),
        )
        if getattr(args, "warm_start_reduce_random", False):
            step_counter = min(step_counter + seeded, target_random_warmup)
            print(f"[td3_llm] Random warmup starts at {step_counter}/{target_random_warmup} after memory seeding.")

    while step_counter < target_random_warmup:
        obs = env.reset()
        done = False
        while not done:
            action = env.action_space.sample()
            next_state, reward, done, info = env.step(action)
            env_pool.push(obs, action, reward, next_state, done)
            obs = next_state
            step_counter += 1
            print(f"===step_counter: {step_counter}")
            
    return step_counter

def train_policy(args, env_pool, agent, total_steps):
    if env_pool.size < args.batch_size:
        return
    state, action, next_state, reward, not_done = env_pool.sample(args.batch_size)
    batch = (state, action, next_state, reward, not_done)
    agent.update_parameters(memory_batch=batch, update=total_steps)

def td3_start(args=None, circuit_name=None, list_min_targets=None):
    import time  
    if args is None:
        args = readParser()
    if circuit_name is None:
        circuit_name = getattr(args, "circuit_name", None)
    if circuit_name is None:
        raise ValueError("circuit_name is required. Pass --circuit_name or call td3_start(circuit_name=...).")
    start_time = time.time()
    # Set random seed
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    # Initial environment
    # env = CircuitEnv(run_id=args.run_id, circuit_name='TwoStage')
    env = CircuitEnv(run_id=args.run_id, circuit_name = circuit_name, list_min_targets=list_min_targets)
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.shape[0]
    # Intial agent
    agent = TD3(state_dim, env.action_space, args)
    # Initial pool for env
    # print("observation_space",env.observation_space)
    # print("action_space",env.action_space)
    env_pool = ReplayBuffer(state_dim, action_dim, max_size=args.replay_size)
    # Training
    train(args, env, agent, env_pool)

    if getattr(args, "warm_start_category", None):
        saved_memory_path = save_best_candidate_record(env, args.warm_start_category)
        if saved_memory_path:
            print(f"[td3_llm] Saved best candidate to category memory: {saved_memory_path}")
        else:
            print("[td3_llm] No finite best candidate available for category memory.")

    # compute and print total runtime
    total_time = time.time() - start_time
    print(f"[TD3 Runner] Training complete. Total runtime: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    summary_path = Path(env.solutions_dir) / "run_summary.json"
    existing_summary = {}
    if summary_path.is_file():
        try:
            with open(summary_path, "r", encoding="utf-8") as summary_file:
                existing_summary = json.load(summary_file)
        except (OSError, json.JSONDecodeError):
            existing_summary = {}

    summary = {
        "run_id": str(args.run_id),
        "circuit_name": str(circuit_name),
        "mode": existing_summary.get("mode", "rl"),
        "llm": existing_summary.get("llm", {
            "calls_total": 0,
            "calls_by_agent": {},
        }),
        "rl": {
            "seed": int(args.seed),
            "total_runtime_seconds": float(total_time),
            "planned_env_steps": int(args.T),
            "warmup_steps": int(args.w),
            "full_warmup_steps": getattr(args, "full_warmup_steps", None),
            "dc_seed_samples": int(getattr(args, "dc_seed_samples", 0)),
            "dc_seed_elites": int(getattr(args, "dc_seed_elites", 0)),
            "dc_seed_method": str(getattr(args, "dc_seed_method", "random")),
            "low_fidelity_strategy": str(getattr(args, "low_fidelity_strategy", "ac_gain")),
            "warm_start_reduce_random": bool(getattr(args, "warm_start_reduce_random", False)),
            "env_steps": int(getattr(env, "env_steps", 0)),
            "full_simulations": int(getattr(env, "full_simulations", 0)),
            "low_fidelity_simulations": int(getattr(env, "low_fidelity_simulations", 0)),
            "best_reward": float(getattr(env, "best_reward", float("-inf"))),
            "best_step": getattr(env, "best_step", None),
            "best_constraints_met": bool(getattr(env, "best_hard_satisfied", False)),
            "best_netlist_path": getattr(env, "best_netlist_path", None),
        },
    }
    try:
        with open(summary_path, "w", encoding="utf-8") as summary_file:
            json.dump(summary, summary_file, indent=2, allow_nan=False)
        print(f"[TD3 Runner] Saved run summary to: {summary_path}")
    except (OSError, TypeError, ValueError) as exc:
        print(f"[TD3 Runner] Failed to save run summary: {exc}")

    best_netlist_path = getattr(env, "best_netlist_path", None)
    if best_netlist_path and os.path.isfile(best_netlist_path):
        csv_folder = Path(best_netlist_path).parent
        save_path = csv_folder / "pure_RL_best_solution.cir"
        shutil.copy2(best_netlist_path, save_path)
        print(
            f"[TD3 Runner] Saved highest-reward netlist "
            f"(reward={env.best_reward:.6g}, constraints_met={env.best_hard_satisfied}) "
            f"to: {save_path}"
        )
    else:
        print("[TD3 Runner] No valid candidate netlist was available to save.")

# td3_start(circuit_name='TwoStage')
# td3_start(circuit_name='9')
if __name__ == "__main__":
    td3_start()
