import json
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import numpy as np

from circuit_env import CircuitEnv
from utils.workflow_metrics import record_llm_call, record_llm_duration


class FullCandidateMetricsTests(unittest.TestCase):
    def test_strict_seed_is_recorded_without_advancing_policy_steps(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_netlist = root / "candidate.cir"
            source_netlist.write_text("* candidate\n", encoding="utf-8")

            env = CircuitEnv.__new__(CircuitEnv)
            env.run_id = "test_run"
            env.circuit_name = "9"
            env.env_steps = 0
            env.episode_steps = 0
            env.full_simulations = 0
            env.low_fidelity_simulations = 2
            env.seed_full_simulations = 0
            env.first_success_full_simulations = None
            env.run_start_time = time.time() - 0.01
            env.time_to_first_solution_seconds = None
            env.time_to_best_solution_seconds = None
            env.best_reward = -np.inf
            env.best_params = None
            env.best_specs = None
            env.best_step = None
            env.best_hard_satisfied = False
            env.best_netlist_path = None
            env.best_source = None
            env.best_netlist_target_path = str(root / "best_so_far.cir")
            env.best_metadata_path = str(root / "best_so_far.json")
            env.all_rl_cir_dir = str(root / "allRLcir")
            Path(env.all_rl_cir_dir).mkdir()
            env.candidate_history = []
            env.simulation_engine = SimpleNamespace(netlist_path=str(source_netlist))

            def evaluate(action):
                env.full_simulations += 1
                env.param_values = {"W": 1.0}
                env.real_specs = {"dc_gain": 12.0}
                env.cur_norm_specs = {"dc_gain": 0.1}

            env.evaluate = evaluate
            env.reward_computation = lambda specs: (1.5, True)
            env._build_observation = lambda specs: np.asarray([0.1], dtype=np.float32)
            strict_records = []
            env._record_strict_solution = lambda reward, source="policy": strict_records.append((reward, source))

            observation, reward, hard_satisfied = env.evaluate_full_candidate(
                np.asarray([0.0], dtype=np.float32),
                source="warm_start_seed",
            )

            self.assertTrue(hard_satisfied)
            self.assertEqual(reward, 1.5)
            self.assertEqual(observation.tolist(), [np.float32(0.1)])
            self.assertEqual(env.env_steps, 0)
            self.assertEqual(env.seed_full_simulations, 1)
            self.assertEqual(env.first_success_full_simulations, 1)
            self.assertIsNotNone(env.time_to_first_solution_seconds)
            self.assertIsNotNone(env.time_to_best_solution_seconds)
            self.assertEqual(env.best_source, "warm_start_seed")
            self.assertEqual(env.candidate_history[0]["source"], "warm_start_seed")
            self.assertEqual(env.candidate_history[0]["full_simulation"], 1)
            self.assertEqual(strict_records, [(1.5, "warm_start_seed")])
            self.assertTrue(Path(env.best_netlist_target_path).is_file())

    def test_llm_call_count_and_duration_accumulate(self):
        with TemporaryDirectory() as temp_dir:
            record_llm_call("run_1", "dc_setter", circuit_name="9", solutions_dir=temp_dir)
            record_llm_duration(
                "run_1",
                "dc_setter",
                1.25,
                solutions_dir=temp_dir,
            )
            record_llm_call("run_1", "dc_setter", circuit_name="9", solutions_dir=temp_dir)
            record_llm_duration(
                "run_1",
                "dc_setter",
                0.75,
                solutions_dir=temp_dir,
            )

            summary_path = Path(temp_dir) / "9" / "run_1" / "run_summary.json"
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["llm"]["calls_total"], 2)
            self.assertEqual(summary["llm"]["calls_by_agent"]["dc_setter"], 2)
            self.assertEqual(summary["llm"]["time_seconds"], 2.0)
            self.assertEqual(summary["llm"]["time_by_agent_seconds"]["dc_setter"], 2.0)


if __name__ == "__main__":
    unittest.main()
