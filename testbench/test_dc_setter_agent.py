import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from genai_agent.data.response_schema import Struct_dc_setter, build_dc_setter_response_schema
from main import make_td3_args
from td3_llm_category_level.dc_setter_agent import (
    _json_candidate,
    build_dc_setter_prompt,
    collect_dc_setter_elites,
    prepare_dc_setter_candidates,
    resolve_category_name,
)


class DCSetterAgentTests(unittest.TestCase):
    def setUp(self):
        self.ranges = {
            "VB1_VAL": {"min": 0.0, "max": 1.2, "step": 0.05},
            "mn1": {"min": 1, "max": 25, "step": 1},
            "wn1": {"min": 0.25e-6, "max": 3.0e-6, "step": 0.25e-6},
        }

    def test_prompt_contains_only_minimal_contract_fields(self):
        prompt = build_dc_setter_prompt(
            "category_1",
            "M1 d g s b nmos",
            [],
            self.ranges,
            2,
            simulation_feedback=[{"candidate_id": "default", "measured": {"dc_gain": 1.0}}],
        )
        self.assertIn('"category"', prompt)
        self.assertIn('"netlist"', prompt)
        self.assertIn('"experience"', prompt)
        self.assertIn('"parameters"', prompt)
        self.assertIn('"simulation_feedback"', prompt)
        self.assertIn("Do not create a monotonic sweep", prompt)
        self.assertNotIn('"full_targets_context"', prompt)

    def test_dynamic_schema_declares_and_preserves_every_parameter(self):
        schema = build_dc_setter_response_schema(self.ranges.keys())
        parameter_properties = schema.model_json_schema()["$defs"]["DCSetterParameters"]["properties"]
        self.assertEqual(set(parameter_properties), set(self.ranges))

        parsed = schema(
            analysis_summary="Bias first.",
            candidates=[
                {
                    "candidate_id": "dc_gain_1",
                    "parameters": {"VB1_VAL": 0.5, "mn1": 2, "wn1": 0.5e-6},
                    "increase_dc_gain": True,
                }
            ],
        )
        self.assertEqual(set(parsed.model_dump()["candidates"][0]["parameters"]), set(self.ranges))

    def test_candidate_log_conversion_handles_numpy_scalars_recursively(self):
        converted = _json_candidate(
            {
                "action": np.asarray([0.1], dtype=np.float32),
                "params": {"Cload": np.float32(1e-12)},
                "specs": {"dc_gain": np.float64(12.0), "counts": [np.int64(2)]},
            }
        )
        self.assertIsInstance(converted["params"]["Cload"], float)
        self.assertIsInstance(converted["specs"]["dc_gain"], float)
        self.assertIsInstance(converted["specs"]["counts"][0], int)

    def test_validation_assigns_ids_quantizes_and_removes_duplicates(self):
        response = Struct_dc_setter(
            analysis_summary="Bias first.",
            candidates=[
                {
                    "candidate_id": "bad_id",
                    "parameters": {"VB1_VAL": 0.11, "mn1": 3.8, "wn1": 0.61e-6},
                    "increase_dc_gain": True,
                },
                {
                    "candidate_id": "duplicate",
                    "parameters": {"VB1_VAL": 0.11, "mn1": 3.8, "wn1": 0.61e-6},
                    "increase_dc_gain": False,
                },
            ],
        )
        candidates, errors = prepare_dc_setter_candidates(response, self.ranges, quantize=True)
        self.assertEqual(errors, [])
        self.assertEqual([item["candidate_id"] for item in candidates], ["dc_gain_1", "dc_gain_2"])
        self.assertEqual(candidates[1]["parameters"]["VB1_VAL"], 0.1)
        self.assertEqual(candidates[1]["parameters"]["mn1"], 4.0)
        self.assertTrue(np.all(candidates[1]["action"] <= 1.0))
        self.assertTrue(np.all(candidates[1]["action"] >= -1.0))

    def test_incomplete_and_out_of_bounds_candidates_are_rejected(self):
        response = {
            "candidates": [
                {"parameters": {"VB1_VAL": 0.5}, "increase_dc_gain": True},
                {
                    "parameters": {"VB1_VAL": 2.0, "mn1": 2, "wn1": 0.5e-6},
                    "increase_dc_gain": True,
                },
            ]
        }
        candidates, errors = prepare_dc_setter_candidates(response, self.ranges)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["source"], "minimum_baseline")
        self.assertEqual(len(errors), 2)

    def test_category_mode_always_configures_setter_and_sobol_fallback(self):
        args = make_td3_args("9", "category_llm_rl", run_id="test_run", category_key="category_1")
        self.assertEqual(args.dc_setter_candidates, 2)
        self.assertEqual(args.dc_setter_rounds, 2)
        self.assertEqual(args.dc_setter_elites, 5)
        self.assertEqual(args.dc_setter_fallback_sobol_samples, 20)

    def test_category_key_resolves_to_human_readable_name(self):
        self.assertIn("Amplifiers", resolve_category_name("category_1"))

    def test_mocked_collection_runs_default_and_two_feedback_rounds(self):
        with TemporaryDirectory() as temp_dir:
            netlist_path = Path(temp_dir) / "final_netlist.cir"
            netlist_path.write_text("M1 d g s b nmos\n", encoding="utf-8")

            class FakeEnv:
                run_id = "test_run"
                circuit_name = "9"
                param_ranges = self.ranges
                simulation_engine = SimpleNamespace(
                    netlist_path=str(netlist_path),
                    parameters={"VB1_VAL": 0.4, "mn1": 1, "wn1": 0.25e-6},
                )

                def __init__(self):
                    self.strategies = []

                def evaluate_low_fidelity(self, action, strategy):
                    self.strategies.append(strategy)
                    params = {
                        name: float(bounds["min"] + ((float(action[index]) + 1.0) / 2.0) * (bounds["max"] - bounds["min"]))
                        for index, (name, bounds) in enumerate(self.param_ranges.items())
                    }
                    params["mn1"] = int(params["mn1"])
                    if strategy == "op_domain":
                        specs = {"op_device_count": 2, "op_alive_ratio": 1.0, "op_saturation_ratio": 1.0}
                    else:
                        specs = {"dc_gain": 10.0 + params["VB1_VAL"]}
                    return {
                        "action": action,
                        "params": params,
                        "specs": specs,
                        "netlist_path": str(netlist_path),
                    }

                def dc_feasibility_reward(self, specs, strategy):
                    return float(specs["op_alive_ratio"] + specs["dc_gain"])

            round_1 = Struct_dc_setter(
                analysis_summary="Bias first.",
                candidates=[
                    {
                        "candidate_id": "r1_a",
                        "parameters": {"VB1_VAL": 0.5, "mn1": 2, "wn1": 0.5e-6},
                        "increase_dc_gain": True,
                    },
                    {
                        "candidate_id": "r1_b",
                        "parameters": {"VB1_VAL": 0.6, "mn1": 2, "wn1": 0.75e-6},
                        "increase_dc_gain": True,
                    },
                ],
            )
            round_2 = Struct_dc_setter(
                analysis_summary="Refine measured direction.",
                candidates=[
                    {
                        "candidate_id": "r2_a",
                        "parameters": {"VB1_VAL": 0.55, "mn1": 3, "wn1": 0.75e-6},
                        "increase_dc_gain": True,
                    },
                    {
                        "candidate_id": "r2_b",
                        "parameters": {"VB1_VAL": 0.45, "mn1": 2, "wn1": 0.5e-6},
                        "increase_dc_gain": False,
                    },
                ],
            )
            env = FakeEnv()
            with patch(
                "td3_llm_category_level.dc_setter_agent.call_dc_setter_agent",
                side_effect=[round_1, round_2],
            ) as call_mock:
                elites = collect_dc_setter_elites(
                    env,
                    category="category_1",
                    candidate_count=2,
                    elite_count=2,
                    round_count=2,
                    min_alive_ratio=0.5,
                )

            self.assertEqual(len(elites), 2)
            self.assertEqual(env.strategies, ["op_domain", "ac_gain"] * 5)
            self.assertEqual(call_mock.call_count, 2)
            first_feedback = call_mock.call_args_list[0].kwargs["simulation_feedback"]
            second_feedback = call_mock.call_args_list[1].kwargs["simulation_feedback"]
            self.assertEqual([item["candidate_id"] for item in first_feedback], ["default"])
            self.assertEqual(len(second_feedback), 3)
            self.assertEqual({item["candidate_id"] for item in second_feedback}, {"default", "dc_gain_1", "dc_gain_2"})


if __name__ == "__main__":
    unittest.main()
