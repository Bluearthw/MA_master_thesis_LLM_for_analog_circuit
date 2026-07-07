import json
import math
import os
import re
from datetime import datetime
from pathlib import Path


MEMORY_VERSION = 1


def _safe_name(value):
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value).strip())
    return cleaned.strip("._") or "uncategorized"


def default_memory_dir(project_root=None):
    root = Path(project_root or os.getcwd())
    return root / "solutions" / "category_memory"


def memory_path(category, memory_dir=None):
    base_dir = Path(memory_dir) if memory_dir else default_memory_dir()
    return base_dir / f"{_safe_name(category)}.jsonl"


def target_signature(env):
    return {
        "targets": list(env.dict_targets.keys()),
        "hard_constraints": list(env.hard_constraints),
        "optimization_targets": list(env.optimization_targets),
        "minimize_targets": list(getattr(env, "list_min_targets", []) or []),
    }


def build_candidate_record(env, category):
    if not getattr(env, "best_params", None):
        return None

    reward = float(env.best_reward)
    if not math.isfinite(reward):
        return None

    return {
        "version": MEMORY_VERSION,
        "saved_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "category": str(category),
        "circuit_name": str(env.circuit_name),
        "run_id": str(env.run_id),
        "state_dim": int(env.observation_space.shape[0]),
        "action_dim": int(env.action_space.shape[0]),
        "param_names": list(env.param_ranges.keys()),
        "target_signature": target_signature(env),
        "reward": reward,
        "constraints_met": bool(env.best_hard_satisfied),
        "params": env._to_serializable(env.best_params),
        "specs": env._to_serializable(env.best_specs or {}),
        "netlist_path": getattr(env, "best_netlist_path", None),
    }


def append_record(record, category=None, memory_dir=None):
    if record is None:
        return None

    path = memory_path(category or record.get("category", "uncategorized"), memory_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as file:
        file.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
    return path


def save_best_candidate_record(env, category, memory_dir=None):
    record = build_candidate_record(env, category)
    return append_record(record, category=category, memory_dir=memory_dir)


def iter_records(category, memory_dir=None):
    path = memory_path(category, memory_dir)
    if not path.is_file():
        return

    with open(path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"[td3_llm] Skipping invalid memory row {path}:{line_number}: {exc}")


def is_compatible(record, env):
    if record.get("version") != MEMORY_VERSION:
        return False
    if int(record.get("state_dim", -1)) != int(env.observation_space.shape[0]):
        return False
    if int(record.get("action_dim", -1)) != int(env.action_space.shape[0]):
        return False
    if list(record.get("param_names", [])) != list(env.param_ranges.keys()):
        return False

    saved_signature = record.get("target_signature", {})
    return list(saved_signature.get("targets", [])) == list(env.dict_targets.keys())
