import json
import math
import os
import re
from datetime import datetime
from pathlib import Path

import numpy as np


TRACE_VERSION = 1


def _safe_name(value):
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value).strip())
    return cleaned.strip("._") or "unknown"


def default_trace_dir(project_root=None):
    root = Path(project_root or os.getcwd())
    return root / "solutions" / "category_memory" / "traces"


def trace_path(category, circuit_name, run_id, trace_dir=None):
    base_dir = Path(trace_dir) if trace_dir else default_trace_dir()
    return (
        base_dir
        / _safe_name(category)
        / _safe_name(circuit_name)
        / f"{_safe_name(run_id)}_trace.json"
    )


def save_run_trace(trace, path=None):
    target_path = Path(path) if path else trace_path(
        trace.get("category", "unknown"),
        trace.get("circuit_name", "unknown"),
        trace.get("run_id", "unknown"),
    )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_suffix(target_path.suffix + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as trace_file:
        json.dump(_to_serializable(trace), trace_file, indent=2, allow_nan=False)
    os.replace(temp_path, target_path)
    return target_path


def validate_run_trace(trace):
    errors = []
    required_fields = [
        "version",
        "saved_at",
        "run_id",
        "circuit_name",
        "category",
        "method",
        "dimensions",
        "targets",
        "rl",
        "best",
        "failed_specs",
        "top_candidates",
        "action_distribution",
        "boundary_clustering",
        "transfer",
    ]
    for field in required_fields:
        if field not in trace:
            errors.append(f"missing required field: {field}")

    if trace.get("version") != TRACE_VERSION:
        errors.append(f"unsupported trace version: {trace.get('version')}")

    dimensions = trace.get("dimensions", {})
    if int(dimensions.get("action_dim", -1)) < 0:
        errors.append("dimensions.action_dim must be non-negative")
    if int(dimensions.get("observation_dim", -1)) < 0:
        errors.append("dimensions.observation_dim must be non-negative")

    rl = trace.get("rl", {})
    for count_field in ("full_simulations", "low_fidelity_simulations"):
        if int(rl.get(count_field, -1)) < 0:
            errors.append(f"rl.{count_field} must be non-negative")

    return {"valid": not errors, "errors": errors}


def build_run_trace(
    env,
    args,
    circuit_name,
    category,
    total_runtime_seconds,
    transfer_plan_path=None,
    run_summary_path=None,
):
    candidate_history = list(getattr(env, "candidate_history", []) or [])
    top_candidates = _top_candidates(candidate_history, limit=10)
    best_specs = getattr(env, "best_specs", None) or {}

    trace = {
        "version": TRACE_VERSION,
        "saved_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "run_id": str(getattr(args, "run_id", getattr(env, "run_id", ""))),
        "circuit_name": str(circuit_name),
        "category": str(category),
        "method": _method_name(args, category),
        "dimensions": {
            "observation_dim": int(getattr(env.observation_space, "shape", [0])[0]),
            "action_dim": int(getattr(env.action_space, "shape", [0])[0]),
        },
        "params": {
            "names": list(getattr(env, "param_ranges", {}).keys()),
            "ranges": _to_serializable(getattr(env, "param_ranges", {})),
        },
        "targets": {
            "names": list(getattr(env, "dict_targets", {}).keys()),
            "values": _to_serializable(getattr(env, "dict_targets", {})),
            "hard_constraints": list(getattr(env, "hard_constraints", []) or []),
            "optimization_targets": list(getattr(env, "optimization_targets", []) or []),
            "minimize_targets": list(getattr(env, "list_min_targets", []) or []),
        },
        "rl": {
            "seed": int(getattr(args, "seed", 0)),
            "planned_env_steps": int(getattr(args, "T", 0)),
            "warmup_steps": int(getattr(args, "w", 0)),
            "full_warmup_steps": getattr(args, "full_warmup_steps", None),
            "env_steps": int(getattr(env, "env_steps", 0)),
            "total_runtime_seconds": float(total_runtime_seconds),
            "full_simulations": int(getattr(env, "full_simulations", 0)),
            "low_fidelity_simulations": int(getattr(env, "low_fidelity_simulations", 0)),
            "first_success_full_simulations": getattr(env, "first_success_full_simulations", None),
            "reward_history": _finite_series(getattr(env, "reward_history", []) or []),
            "best_reward_progression": _running_max(getattr(env, "reward_history", []) or []),
        },
        "best": {
            "reward": _finite_or_none(getattr(env, "best_reward", None)),
            "step": getattr(env, "best_step", None),
            "strict_pass": bool(getattr(env, "best_hard_satisfied", False)),
            "params": _to_serializable(getattr(env, "best_params", None) or {}),
            "metrics": _to_serializable(best_specs),
            "netlist_path": getattr(env, "best_netlist_path", None),
        },
        "failed_specs": _failed_specs(env, best_specs),
        "top_candidates": top_candidates,
        "action_distribution": _action_distribution(candidate_history),
        "boundary_clustering": _boundary_clustering(
            top_candidates,
            getattr(env, "param_ranges", {}) or {},
        ),
        "failure_patterns": _failure_patterns(candidate_history),
        "transfer": {
            "warm_start_category": getattr(args, "warm_start_category", None),
            "warm_start_records": int(getattr(args, "warm_start_records", 0)),
            "warm_start_reduce_random": bool(getattr(args, "warm_start_reduce_random", False)),
            "dc_seed_samples": int(getattr(args, "dc_seed_samples", 0)),
            "dc_seed_elites": int(getattr(args, "dc_seed_elites", 0)),
            "dc_seed_method": str(getattr(args, "dc_seed_method", "random")),
            "low_fidelity_strategy": str(getattr(args, "low_fidelity_strategy", "ac_gain")),
            "transfer_plan_path": str(transfer_plan_path) if transfer_plan_path else None,
            "run_summary_path": str(run_summary_path) if run_summary_path else None,
        },
    }
    trace["validation"] = validate_run_trace(trace)
    return trace


def _method_name(args, category):
    if getattr(args, "warm_start_category", None):
        return "category_feedback_td3"
    if int(getattr(args, "dc_seed_samples", 0) or 0) > 0:
        return "low_fidelity_seed_td3"
    if str(category).startswith("category_"):
        return "td3"
    return "td3"


def _failed_specs(env, best_specs):
    failed = []
    targets = getattr(env, "dict_targets", {}) or {}
    hard_constraints = getattr(env, "hard_constraints", []) or []
    minimize_targets = set(getattr(env, "list_min_targets", []) or [])

    for name in hard_constraints:
        target = targets.get(name)
        measured = best_specs.get(name)
        met = _spec_met(name, measured, target, minimize_targets)
        if met:
            continue
        failed.append(
            {
                "name": str(name),
                "target": _finite_or_none(target),
                "measured": _finite_or_none(measured),
                "direction": "minimize" if name in minimize_targets else "maximize",
                "violation_margin": _violation_margin(name, measured, target, minimize_targets),
            }
        )
    return failed


def _spec_met(name, measured, target, minimize_targets):
    measured_value = _finite_or_none(measured)
    target_value = _finite_or_none(target)
    if measured_value is None or target_value is None:
        return False
    if name in minimize_targets:
        return measured_value <= target_value
    return measured_value >= target_value


def _violation_margin(name, measured, target, minimize_targets):
    measured_value = _finite_or_none(measured)
    target_value = _finite_or_none(target)
    if measured_value is None or target_value is None:
        return None
    denom = max(abs(target_value), 1e-12)
    if name in minimize_targets:
        return max((measured_value - target_value) / denom, 0.0)
    return max((target_value - measured_value) / denom, 0.0)


def _top_candidates(candidate_history, limit=10):
    candidates = []
    for candidate in candidate_history:
        reward = _finite_or_none(candidate.get("reward"))
        if reward is None:
            continue
        candidates.append(
            {
                "step": candidate.get("step"),
                "reward": reward,
                "strict_pass": bool(candidate.get("strict_pass", False)),
                "action": _to_serializable(candidate.get("action", [])),
                "params": _to_serializable(candidate.get("params", {})),
                "metrics": _to_serializable(candidate.get("metrics", {})),
            }
        )
    candidates.sort(key=lambda item: item["reward"], reverse=True)
    return candidates[:limit]


def _action_distribution(candidate_history):
    actions = [
        np.asarray(candidate.get("action", []), dtype=np.float64).reshape(-1)
        for candidate in candidate_history
        if candidate.get("action") is not None
    ]
    actions = [action for action in actions if action.size > 0]
    if not actions:
        return {
            "count": 0,
            "mean": [],
            "std": [],
            "min": [],
            "max": [],
            "mean_abs": [],
        }

    min_size = min(action.size for action in actions)
    matrix = np.vstack([action[:min_size] for action in actions])
    return {
        "count": int(matrix.shape[0]),
        "mean": _to_serializable(np.mean(matrix, axis=0)),
        "std": _to_serializable(np.std(matrix, axis=0)),
        "min": _to_serializable(np.min(matrix, axis=0)),
        "max": _to_serializable(np.max(matrix, axis=0)),
        "mean_abs": _to_serializable(np.mean(np.abs(matrix), axis=0)),
    }


def _boundary_clustering(top_candidates, param_ranges):
    result = {}
    if not top_candidates:
        return result

    total = len(top_candidates)
    for name, param_range in param_ranges.items():
        values = []
        for candidate in top_candidates:
            params = candidate.get("params", {})
            if name in params:
                value = _finite_or_none(params[name])
                if value is not None:
                    values.append(value)
        if not values:
            continue

        min_value = _finite_or_none(param_range.get("min"))
        max_value = _finite_or_none(param_range.get("max"))
        if min_value is None or max_value is None:
            continue

        tolerance = max(abs(max_value - min_value) * 1e-6, 1e-12)
        at_min = sum(1 for value in values if abs(value - min_value) <= tolerance)
        at_max = sum(1 for value in values if abs(value - max_value) <= tolerance)
        result[str(name)] = {
            "top_candidate_count": total,
            "observed_count": len(values),
            "at_min_count": int(at_min),
            "at_max_count": int(at_max),
            "at_min_fraction": float(at_min / max(len(values), 1)),
            "at_max_fraction": float(at_max / max(len(values), 1)),
            "top_min": min(values),
            "top_max": max(values),
        }
    return result


def _failure_patterns(candidate_history):
    missing_metrics = {}
    invalid_rewards = 0
    for candidate in candidate_history:
        if _finite_or_none(candidate.get("reward")) is None:
            invalid_rewards += 1
        metrics = candidate.get("metrics", {}) or {}
        for name, value in metrics.items():
            if _finite_or_none(value) is None:
                missing_metrics[str(name)] = missing_metrics.get(str(name), 0) + 1
    return {
        "candidate_count": len(candidate_history),
        "invalid_reward_count": invalid_rewards,
        "missing_metric_counts": missing_metrics,
    }


def _running_max(values):
    progression = []
    best = None
    for value in values:
        finite_value = _finite_or_none(value)
        if finite_value is None:
            continue
        best = finite_value if best is None else max(best, finite_value)
        progression.append(best)
    return progression


def _finite_series(values):
    return [value for value in (_finite_or_none(item) for item in values) if value is not None]


def _finite_or_none(value):
    try:
        numeric = float(np.asarray(value).reshape(-1)[0])
    except (TypeError, ValueError, IndexError):
        return None
    if not math.isfinite(numeric):
        return None
    return numeric


def _to_serializable(value):
    if isinstance(value, dict):
        return {str(key): _to_serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_serializable(item) for item in value]
    if isinstance(value, np.ndarray):
        return _to_serializable(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value
