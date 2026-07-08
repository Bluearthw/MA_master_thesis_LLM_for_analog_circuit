import numpy as np
import json
from pathlib import Path

from .category_memory import is_compatible, iter_records


def params_to_action(params, param_ranges):
    action = []
    for name, bounds in param_ranges.items():
        if name not in params:
            raise KeyError(f"Missing saved parameter '{name}'")

        min_val = float(bounds["min"])
        max_val = float(bounds["max"])
        if max_val == min_val:
            action.append(0.0)
            continue

        value = float(params[name])
        normalized = 2.0 * (value - min_val) / (max_val - min_val) - 1.0
        action.append(float(np.clip(normalized, -1.0, 1.0)))

    return np.asarray(action, dtype=np.float32)


def _evaluate_seed_action(env, action):
    env.evaluate(action)
    reward, hard_satisfied = env.reward_computation(env.cur_norm_specs)
    env._save_best_candidate(reward, hard_satisfied)
    observation = env._build_observation(env.cur_norm_specs)
    return observation, reward


def seed_replay_from_category_memory(env, replay_buffer, category, max_records=20, memory_dir=None):
    compatible = []
    for record in iter_records(category, memory_dir):
        if is_compatible(record, env):
            compatible.append(record)

    compatible.sort(key=lambda item: float(item.get("reward", -np.inf)), reverse=True)
    selected = compatible[: max(0, int(max_records))]

    seeded = 0
    for record in selected:
        try:
            action = params_to_action(record.get("params", {}), env.param_ranges)
            next_observation, reward = _evaluate_seed_action(env, action)
        except Exception as exc:
            print(f"[td3_llm] Failed to seed memory record: {exc}")
            continue

        state = np.zeros(env.observation_space.shape[0], dtype=np.float32)
        done = True
        replay_buffer.push(state, action, reward, next_observation, done)
        seeded += 1

    if category:
        print(
            f"[td3_llm] Seeded {seeded} replay transitions from "
            f"{len(compatible)} compatible '{category}' memory records."
        )
    return seeded


def _sample_actions(action_space, count, method="random", seed=None):
    count = max(0, int(count))
    action_dim = int(action_space.shape[0])
    if count == 0:
        return np.zeros((0, action_dim), dtype=np.float32)

    if method == "sobol":
        try:
            from scipy.stats import qmc

            sampler = qmc.Sobol(d=action_dim, scramble=True, seed=seed)
            unit_samples = sampler.random(count)
            low = np.asarray(action_space.low, dtype=np.float32)
            high = np.asarray(action_space.high, dtype=np.float32)
            return (low + unit_samples * (high - low)).astype(np.float32)
        except Exception as exc:
            print(f"[td3_llm] Sobol sampling unavailable, falling back to random: {exc}")

    rng = np.random.default_rng(seed)
    return rng.uniform(action_space.low, action_space.high, size=(count, action_dim)).astype(np.float32)


def _to_jsonable_candidate(candidate):
    return {
        "reward": float(candidate.get("reward", 0.0)),
        "strategy": candidate.get("strategy"),
        "action": np.asarray(candidate.get("action", []), dtype=np.float32).tolist(),
        "params": _to_jsonable_value(candidate.get("params", {})),
        "specs": _to_jsonable_value(candidate.get("specs", {})),
        "netlist_path": candidate.get("netlist_path"),
    }


def _to_jsonable_value(value):
    if isinstance(value, dict):
        return {str(key): _to_jsonable_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable_value(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


def _write_json(path, payload):
    if path is None:
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, allow_nan=False)


def collect_low_fidelity_elites(env, sample_count, elite_count, method="random", seed=None, log_path=None, strategy="ac_gain"):
    actions = _sample_actions(env.action_space, sample_count, method=method, seed=seed)
    candidates = []
    for index, action in enumerate(actions, start=1):
        try:
            candidate = env.evaluate_low_fidelity(action, strategy=strategy)
            candidates.append(candidate)
            print(
                f"[td3_llm] {strategy} sample {index}/{len(actions)} "
                f"reward={candidate['reward']:.6g}"
            )
        except Exception as exc:
            print(f"[td3_llm] {strategy} sample {index}/{len(actions)} failed: {exc}")

    candidates.sort(key=lambda item: float(item.get("reward", -np.inf)), reverse=True)
    selected = candidates[: max(0, int(elite_count))]
    print(
        f"[td3_llm] Selected {len(selected)} {strategy} elite candidates "
        f"from {len(candidates)} successful low-fidelity samples."
    )

    _write_json(
        log_path,
        {
            "circuit_name": str(getattr(env, "circuit_name", "")),
            "run_id": str(getattr(env, "run_id", "")),
            "sample_count": int(sample_count),
            "elite_count": int(elite_count),
            "method": str(method),
            "strategy": str(strategy),
            "seed": seed,
            "num_successful_samples": len(candidates),
            "candidates": [_to_jsonable_candidate(item) for item in candidates],
            "selected_elites": [_to_jsonable_candidate(item) for item in selected],
        },
    )
    return selected


def seed_replay_from_low_fidelity_elites(env, replay_buffer, elites, log_path=None):
    seeded = 0
    records = []
    for elite in elites:
        action = np.asarray(elite["action"], dtype=np.float32)
        try:
            next_observation, reward = _evaluate_seed_action(env, action)
        except Exception as exc:
            print(f"[td3_llm] Failed full evaluation for OP/DC elite: {exc}")
            continue

        state = np.zeros(env.observation_space.shape[0], dtype=np.float32)
        done = True
        replay_buffer.push(state, action, reward, next_observation, done)
        seeded += 1
        records.append(
            {
                "low_fidelity_reward": float(elite.get("reward", 0.0)),
                "full_reward": float(np.asarray(reward).reshape(-1)[0]),
                "action": action.tolist(),
                "next_observation": np.asarray(next_observation, dtype=np.float32).tolist(),
                "done": done,
            }
        )

    print(f"[td3_llm] Seeded {seeded} full-reward transitions from low-fidelity elites.")
    _write_json(
        log_path,
        {
            "circuit_name": str(getattr(env, "circuit_name", "")),
            "run_id": str(getattr(env, "run_id", "")),
            "seeded": seeded,
            "records": records,
        },
    )
    return seeded
