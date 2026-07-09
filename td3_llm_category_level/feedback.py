import json
import math
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

from .trace import default_trace_dir, validate_run_trace


FEEDBACK_VERSION = 1


def default_feedback_dir(project_root=None):
    root = Path(project_root or os.getcwd())
    return root / "solutions" / "category_memory" / "feedback"


def feedback_path(summary, feedback_dir=None):
    base_dir = Path(feedback_dir) if feedback_dir else default_feedback_dir()
    return (
        base_dir
        / str(summary.get("category", "unknown"))
        / str(summary.get("circuit_name", "unknown"))
        / f"{summary.get('run_id', 'unknown')}_feedback.json"
    )


def iter_trace_paths(category=None, trace_dir=None):
    base_dir = Path(trace_dir) if trace_dir else default_trace_dir()
    if category:
        base_dir = base_dir / str(category)
    if not base_dir.exists():
        return
    yield from base_dir.rglob("*_trace.json")


def load_trace(path):
    with open(path, "r", encoding="utf-8") as trace_file:
        return json.load(trace_file)


def analyze_trace(trace):
    validation = validate_run_trace(trace)
    reward_history = _finite_list(trace.get("rl", {}).get("reward_history", []))
    failed_specs = sorted(
        trace.get("failed_specs", []),
        key=lambda item: float(item.get("violation_margin") or 0.0),
        reverse=True,
    )

    summary = {
        "version": FEEDBACK_VERSION,
        "saved_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "source_trace_version": trace.get("version"),
        "trace_valid": bool(validation["valid"]),
        "trace_errors": list(validation["errors"]),
        "run_id": str(trace.get("run_id", "")),
        "circuit_name": str(trace.get("circuit_name", "")),
        "category": str(trace.get("category", "")),
        "method": str(trace.get("method", "")),
        "strict_pass": bool(trace.get("best", {}).get("strict_pass", False)),
        "best_reward": _finite_or_none(trace.get("best", {}).get("reward")),
        "dimensions": dict(trace.get("dimensions", {})),
        "convergence": analyze_convergence(reward_history),
        "failed_specs": failed_specs,
        "failed_spec_ranking": [
            {
                "name": item.get("name"),
                "violation_margin": _finite_or_none(item.get("violation_margin")),
                "direction": item.get("direction"),
            }
            for item in failed_specs
        ],
        "boundary_analysis": analyze_boundary_clustering(trace.get("boundary_clustering", {})),
        "top_parameter_patterns": extract_top_parameter_patterns(trace.get("top_candidates", [])),
        "low_fidelity_analysis": analyze_low_fidelity_usefulness(trace),
        "memory_transfer_analysis": analyze_memory_transfer(trace),
        "action_analysis": analyze_action_distribution(trace.get("action_distribution", {})),
        "avoid_regions": extract_avoid_regions(trace),
    }
    summary["recommendations"] = build_recommendations(summary)
    return summary


def save_feedback_summary(summary, path=None, feedback_dir=None):
    target_path = Path(path) if path else feedback_path(summary, feedback_dir=feedback_dir)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_suffix(target_path.suffix + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as feedback_file:
        json.dump(_to_serializable(summary), feedback_file, indent=2, allow_nan=False)
    os.replace(temp_path, target_path)
    return target_path


def analyze_trace_file(path, feedback_dir=None):
    trace = load_trace(path)
    summary = analyze_trace(trace)
    return summary, save_feedback_summary(summary, feedback_dir=feedback_dir)


def analyze_trace_directory(category=None, trace_dir=None, feedback_dir=None):
    results = []
    for path in iter_trace_paths(category=category, trace_dir=trace_dir) or []:
        summary = analyze_trace(load_trace(path))
        saved_path = save_feedback_summary(summary, feedback_dir=feedback_dir)
        results.append({"trace_path": str(path), "feedback_path": str(saved_path), "summary": summary})
    return results


def analyze_convergence(reward_history):
    if not reward_history:
        return {
            "status": "no_data",
            "reason": "no finite reward history",
            "reward_count": 0,
            "best_progression": [],
            "recent_improvement": None,
            "stagnant": False,
        }

    best_progression = []
    best = None
    for reward in reward_history:
        best = reward if best is None else max(best, reward)
        best_progression.append(best)

    if len(best_progression) < 3:
        return {
            "status": "early",
            "reason": "fewer than 3 reward points",
            "reward_count": len(reward_history),
            "best_progression": best_progression,
            "recent_improvement": None,
            "stagnant": False,
        }

    recent = best_progression[-3:]
    recent_improvement = recent[-1] - recent[0]
    scale = max(abs(recent[0]), 1.0)
    normalized_improvement = recent_improvement / scale
    stagnant = abs(normalized_improvement) < 0.01

    if stagnant:
        status = "stagnant"
        reason = "best reward improved less than 1 percent over last 3 samples"
    elif normalized_improvement > 0.05:
        status = "improving"
        reason = "best reward improved more than 5 percent over last 3 samples"
    else:
        status = "progressing"
        reason = "best reward still improving but slowly"

    return {
        "status": status,
        "reason": reason,
        "reward_count": len(reward_history),
        "best_progression": best_progression,
        "recent_improvement": recent_improvement,
        "normalized_recent_improvement": normalized_improvement,
        "stagnant": stagnant,
    }


def analyze_boundary_clustering(boundary_clustering):
    analysis = {}
    for name, data in (boundary_clustering or {}).items():
        at_min = float(data.get("at_min_fraction") or 0.0)
        at_max = float(data.get("at_max_fraction") or 0.0)
        if at_min >= 0.4:
            recommendation = "expand_lower_or_unbias_min"
            severity = "high"
        elif at_max >= 0.4:
            recommendation = "expand_upper_or_unbias_max"
            severity = "high"
        elif at_min + at_max <= 0.1:
            recommendation = "keep_range"
            severity = "low"
        else:
            recommendation = "monitor_boundary"
            severity = "medium"
        analysis[str(name)] = {
            "severity": severity,
            "recommendation": recommendation,
            "at_min_fraction": at_min,
            "at_max_fraction": at_max,
            "observed_count": int(data.get("observed_count") or 0),
            "top_min": _finite_or_none(data.get("top_min")),
            "top_max": _finite_or_none(data.get("top_max")),
        }
    return analysis


def extract_top_parameter_patterns(top_candidates, limit=5):
    values_by_param = defaultdict(list)
    for candidate in top_candidates[:limit]:
        for name, value in (candidate.get("params", {}) or {}).items():
            finite_value = _finite_or_none(value)
            if finite_value is not None:
                values_by_param[str(name)].append(finite_value)

    patterns = {}
    for name, values in values_by_param.items():
        rounded_counts = Counter(round(value, 12) for value in values)
        patterns[name] = {
            "count": len(values),
            "mean": float(np.mean(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "most_common": [
                {"value": value, "count": count}
                for value, count in rounded_counts.most_common(3)
            ],
        }
    return patterns


def analyze_low_fidelity_usefulness(trace):
    rl = trace.get("rl", {}) or {}
    transfer = trace.get("transfer", {}) or {}
    low_count = int(rl.get("low_fidelity_simulations") or 0)
    full_count = int(rl.get("full_simulations") or 0)
    first_success = rl.get("first_success_full_simulations")
    strict_pass = bool(trace.get("best", {}).get("strict_pass", False))
    dc_seed_samples = int(transfer.get("dc_seed_samples") or 0)

    if low_count == 0 or dc_seed_samples == 0:
        verdict = "not_used"
        reason = "no low-fidelity seeding was used"
    elif strict_pass and first_success is not None and first_success <= max(3, full_count // 2):
        verdict = "helpful"
        reason = "strict pass appeared early relative to full simulations"
    elif low_count > full_count and not strict_pass:
        verdict = "costly_uncertain"
        reason = "low-fidelity calls exceeded full simulations without strict pass"
    else:
        verdict = "uncertain"
        reason = "insufficient evidence to estimate low-fidelity value"

    return {
        "verdict": verdict,
        "reason": reason,
        "low_fidelity_simulations": low_count,
        "full_simulations": full_count,
        "dc_seed_samples": dc_seed_samples,
        "dc_seed_elites": int(transfer.get("dc_seed_elites") or 0),
        "strategy": transfer.get("low_fidelity_strategy"),
    }


def analyze_memory_transfer(trace):
    transfer = trace.get("transfer", {}) or {}
    warm_records = int(transfer.get("warm_start_records") or 0)
    strict_pass = bool(trace.get("best", {}).get("strict_pass", False))
    convergence = analyze_convergence(_finite_list(trace.get("rl", {}).get("reward_history", [])))

    if warm_records <= 0:
        verdict = "not_used"
        reason = "no category memory records requested"
    elif strict_pass or convergence.get("status") == "improving":
        verdict = "possibly_helpful"
        reason = "memory was used and run showed pass or improving rewards"
    elif convergence.get("status") == "stagnant":
        verdict = "possible_negative_transfer"
        reason = "memory was used but reward stagnated"
    else:
        verdict = "uncertain"
        reason = "memory was used but outcome is inconclusive"

    return {
        "verdict": verdict,
        "reason": reason,
        "warm_start_category": transfer.get("warm_start_category"),
        "warm_start_records": warm_records,
    }


def analyze_action_distribution(action_distribution):
    count = int(action_distribution.get("count") or 0)
    mean_abs = _finite_list(action_distribution.get("mean_abs", []))
    if not mean_abs:
        return {"count": count, "saturated_action_indices": [], "verdict": "no_data"}

    saturated = [index for index, value in enumerate(mean_abs) if value >= 0.85]
    verdict = "possible_over_constraint" if saturated else "diverse"
    return {
        "count": count,
        "saturated_action_indices": saturated,
        "mean_abs": mean_abs,
        "verdict": verdict,
    }


def extract_avoid_regions(trace):
    regions = []
    if trace.get("best", {}).get("strict_pass", False):
        return regions
    for candidate in trace.get("top_candidates", [])[-3:]:
        reward = _finite_or_none(candidate.get("reward"))
        if reward is None or reward > -1.0:
            continue
        regions.append(
            {
                "reason": "low_reward_top_candidate_tail",
                "reward": reward,
                "params": candidate.get("params", {}),
            }
        )
    return regions


def build_recommendations(summary):
    recommendations = []

    if summary["convergence"].get("stagnant"):
        recommendations.append(
            {
                "type": "increase_exploration",
                "severity": "medium",
                "reason": summary["convergence"].get("reason"),
            }
        )

    for spec in summary.get("failed_spec_ranking", [])[:3]:
        if spec.get("violation_margin") is not None:
            recommendations.append(
                {
                    "type": "increase_spec_priority",
                    "target": spec.get("name"),
                    "severity": "high" if spec.get("violation_margin", 0.0) >= 0.2 else "medium",
                    "reason": "hard constraint remains violated in best candidate",
                }
            )

    for name, analysis in summary.get("boundary_analysis", {}).items():
        if analysis.get("severity") == "high":
            recommendations.append(
                {
                    "type": analysis.get("recommendation"),
                    "param": name,
                    "severity": "medium",
                    "reason": "top candidates cluster at parameter boundary",
                }
            )

    low_fidelity = summary.get("low_fidelity_analysis", {})
    if low_fidelity.get("verdict") == "costly_uncertain":
        recommendations.append(
            {
                "type": "reduce_or_skip_low_fidelity",
                "severity": "medium",
                "reason": low_fidelity.get("reason"),
            }
        )

    memory = summary.get("memory_transfer_analysis", {})
    if memory.get("verdict") == "possible_negative_transfer":
        recommendations.append(
            {
                "type": "reduce_memory_transfer",
                "severity": "medium",
                "reason": memory.get("reason"),
            }
        )

    action = summary.get("action_analysis", {})
    if action.get("verdict") == "possible_over_constraint":
        recommendations.append(
            {
                "type": "increase_exploration",
                "severity": "medium",
                "reason": "actions are concentrated near normalized boundaries",
                "action_indices": action.get("saturated_action_indices", []),
            }
        )

    return recommendations


def _finite_list(values):
    result = []
    for value in values or []:
        finite_value = _finite_or_none(value)
        if finite_value is not None:
            result.append(finite_value)
    return result


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
