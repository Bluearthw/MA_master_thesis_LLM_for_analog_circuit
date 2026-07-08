import argparse
import json
from pathlib import Path


def _read_json(path):
    if not path.is_file():
        return None
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _load_run(solutions_dir, run_id):
    run_dir = solutions_dir / run_id
    summary = _read_json(run_dir / "run_summary.json") or {}
    rl_summary = summary.get("rl", summary)
    best = _read_json(run_dir / "best_so_far.json") or {}
    candidates = _read_json(run_dir / "warm_start" / "op_dc_candidates.json") or {}
    seeded = _read_json(run_dir / "warm_start" / "op_dc_seeded_transitions.json") or {}

    return {
        "run_id": run_id,
        "runtime_s": rl_summary.get("total_runtime_seconds"),
        "env_steps": rl_summary.get("env_steps"),
        "full_sims": rl_summary.get("full_simulations"),
        "low_fidelity_sims": rl_summary.get("low_fidelity_simulations", 0),
        "cheap_samples": candidates.get("num_successful_samples", 0),
        "seeded_elites": seeded.get("seeded", 0),
        "best_reward": best.get("reward", rl_summary.get("best_reward")),
        "best_step": best.get("simulation_step", rl_summary.get("best_step")),
        "constraints_met": best.get("constraints_met", rl_summary.get("best_constraints_met")),
        "specs": best.get("specs", {}),
    }


def _fmt(value):
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def build_markdown(rows):
    headers = [
        "run_id",
        "runtime_s",
        "full_sims",
        "low_fidelity_sims",
        "cheap_samples",
        "seeded_elites",
        "best_reward",
        "best_step",
        "constraints_met",
        "dc_gain",
        "bandwidth",
        "psrr",
        "input_total_noise",
        "slew_rate",
        "current",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        specs = row.get("specs", {})
        values = []
        for header in headers:
            if header in specs:
                values.append(_fmt(specs.get(header)))
            else:
                values.append(_fmt(row.get(header)))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Summarize TD3 comparison runs.")
    parser.add_argument("run_ids", nargs="+", help="solution run IDs to compare")
    parser.add_argument("--solutions_dir", default="solutions", help="solutions directory")
    parser.add_argument("--output", default=None, help="optional markdown output path")
    args = parser.parse_args()

    solutions_dir = Path(args.solutions_dir)
    rows = [_load_run(solutions_dir, run_id) for run_id in args.run_ids]
    markdown = build_markdown(rows)
    print(markdown)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
