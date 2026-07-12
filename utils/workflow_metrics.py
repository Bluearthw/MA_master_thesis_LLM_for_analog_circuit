import json
from pathlib import Path


def _summary_path(run_id, solutions_dir="solutions"):
    return Path(solutions_dir) / str(run_id) / "run_summary.json"


def _load_summary(path):
    if not path.is_file():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}


def _save_summary(path, summary):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, allow_nan=False)


def record_llm_call(run_id, agent_name, circuit_name=None, mode=None, solutions_dir="solutions"):
    """Increment LLM call counters in the run summary without touching RL metrics."""
    if not run_id or not agent_name:
        return

    path = _summary_path(run_id, solutions_dir=solutions_dir)
    summary = _load_summary(path)
    summary.setdefault("run_id", str(run_id))
    if circuit_name is not None:
        summary.setdefault("circuit_name", str(circuit_name))
    if mode is not None:
        summary.setdefault("mode", str(mode))

    llm = summary.setdefault("llm", {})
    calls_by_agent = llm.setdefault("calls_by_agent", {})
    calls_by_agent[str(agent_name)] = int(calls_by_agent.get(str(agent_name), 0)) + 1
    llm["calls_total"] = int(llm.get("calls_total", 0)) + 1

    summary.setdefault("rl", {})
    _save_summary(path, summary)


def record_llm_duration(run_id, agent_name, duration_seconds, solutions_dir="solutions"):
    """Accumulate model-request duration for one LLM call attempt."""
    if not run_id or not agent_name:
        return

    path = _summary_path(run_id, solutions_dir=solutions_dir)
    summary = _load_summary(path)
    llm = summary.setdefault("llm", {})
    duration = max(0.0, float(duration_seconds))
    llm["time_seconds"] = float(llm.get("time_seconds", 0.0)) + duration
    time_by_agent = llm.setdefault("time_by_agent_seconds", {})
    agent_key = str(agent_name)
    time_by_agent[agent_key] = float(time_by_agent.get(agent_key, 0.0)) + duration
    _save_summary(path, summary)
