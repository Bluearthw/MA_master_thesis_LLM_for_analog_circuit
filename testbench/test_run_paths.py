import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from utils.file_utils import save_solutions_csv
from utils.plotting import plotLearning
from utils.run_paths import resolve_solution_run_dir, run_artifact_dir


class RunPathTests(unittest.TestCase):
    def test_run_artifact_dir_groups_runs_by_circuit(self):
        self.assertEqual(
            run_artifact_dir("solutions", "9", "run_1"),
            Path("solutions") / "9" / "run_1",
        )

    def test_resolver_finds_nested_and_legacy_runs(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            nested = root / "9" / "nested_run"
            legacy = root / "legacy_run"
            nested.mkdir(parents=True)
            legacy.mkdir()

            self.assertEqual(resolve_solution_run_dir(root, "nested_run"), nested)
            self.assertEqual(resolve_solution_run_dir(root, "legacy_run"), legacy)

    def test_writers_use_explicit_nested_run_directories(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            solutions_dir = root / "solutions" / "9" / "run_1"
            figures_dir = root / "output_figs" / "9" / "run_1"

            csv_path = save_solutions_csv(
                "run_1",
                1,
                {"W": 1.0},
                {"dc_gain": 10.0},
                0.0,
                solutions_dir=solutions_dir,
            )
            plotLearning([0.0], "run_1", output_dir=figures_dir)

            self.assertEqual(Path(csv_path).parent, solutions_dir)
            self.assertTrue(Path(csv_path).is_file())
            self.assertTrue((figures_dir / "average_score.png").is_file())


if __name__ == "__main__":
    unittest.main()
