import json
import os
from pathlib import Path


def build_repair_plan(feedback_summary=None, feedback_transfer_plan=None):
    feedback_summary = feedback_summary or {}
    feedback_transfer_plan = feedback_transfer_plan or {}
    actions = []

    convergence = feedback_summary.get("convergence", {})
    if convergence.get("stagnant"):
        actions.append(
            _action(
                "increase_exploration",
                "medium",
                "reward stagnation detected",
                controls={"noise_sigma_min": 0.2},
            )
        )

    low_fidelity = feedback_summary.get("low_fidelity_analysis", {})
    if low_fidelity.get("verdict") == "costly_uncertain":
        actions.append(
            _action(
                "switch_low_fidelity",
                "medium",
                low_fidelity.get("reason", "low-fidelity cost is not justified"),
                controls={"mode": "skip"},
            )
        )

    memory = feedback_summary.get("memory_transfer_analysis", {})
    if memory.get("verdict") == "possible_negative_transfer":
        actions.append(
            _action(
                "reduce_memory_transfer",
                "medium",
                memory.get("reason", "category memory appears harmful"),
                controls={"warm_start_records_max": 5},
            )
        )

    for recommendation in feedback_summary.get("recommendations", []):
        recommendation_type = recommendation.get("type")
        if recommendation_type in ("expand_upper_or_unbias_max", "expand_lower_or_unbias_min"):
            actions.append(
                _action(
                    "unbias_boundary_param",
                    recommendation.get("severity", "medium"),
                    recommendation.get("reason", "top candidates cluster at boundary"),
                    controls={
                        "param": recommendation.get("param"),
                        "direction": recommendation_type,
                    },
                )
            )
        elif recommendation_type == "increase_spec_priority":
            actions.append(
                _action(
                    "increase_spec_priority",
                    recommendation.get("severity", "medium"),
                    recommendation.get("reason", "hard spec remains violated"),
                    controls={"target": recommendation.get("target")},
                )
            )

    if feedback_transfer_plan.get("memory_policy", {}).get("mode") == "reduce":
        actions.append(
            _action(
                "reduce_memory_transfer",
                "medium",
                feedback_transfer_plan["memory_policy"].get("reason", "transfer plan reduced memory"),
                controls={"warm_start_records_max": 5},
            )
        )

    if feedback_transfer_plan.get("low_fidelity_policy_override", {}).get("mode") == "skip":
        actions.append(
            _action(
                "switch_low_fidelity",
                "medium",
                feedback_transfer_plan["low_fidelity_policy_override"].get("reason", "transfer plan skipped low-fidelity"),
                controls={"mode": "skip"},
            )
        )

    actions = _dedupe_actions(actions)
    return {
        "source": "deterministic_repair_planner",
        "triggered": bool(actions),
        "actions": actions,
        "fallback": _fallback_policy(actions),
    }


def apply_repair_plan_to_args(args, repair_plan):
    applied = []
    for action in repair_plan.get("actions", []):
        controls = action.get("controls", {})
        action_type = action.get("type")
        if action_type == "increase_exploration":
            args.noise_sigma = max(float(getattr(args, "noise_sigma", 0.1)), float(controls.get("noise_sigma_min", 0.2)))
            applied.append(action_type)
        elif action_type == "switch_low_fidelity" and controls.get("mode") == "skip":
            args.dc_seed_samples = 0
            args.dc_seed_elites = 0
            applied.append(action_type)
        elif action_type == "reduce_memory_transfer":
            args.warm_start_records = min(
                int(getattr(args, "warm_start_records", 0) or 0),
                int(controls.get("warm_start_records_max", 5)),
            )
            applied.append(action_type)

    repair_plan["applied_controls"] = applied
    return args


def save_repair_plan(plan, path):
    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_suffix(target_path.suffix + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as plan_file:
        json.dump(plan, plan_file, indent=2, allow_nan=False)
    os.replace(temp_path, target_path)
    return target_path


def _action(action_type, severity, reason, controls=None):
    return {
        "type": action_type,
        "severity": severity,
        "reason": reason,
        "controls": controls or {},
    }


def _dedupe_actions(actions):
    seen = set()
    result = []
    for action in actions:
        key = (action.get("type"), json.dumps(action.get("controls", {}), sort_keys=True))
        if key in seen:
            continue
        seen.add(key)
        result.append(action)
    return result


def _fallback_policy(actions):
    if not actions:
        return {"mode": "none", "reason": "no repair trigger"}
    high_count = sum(1 for action in actions if action.get("severity") == "high")
    if high_count >= 2:
        return {
            "mode": "baseline_td3",
            "reason": "multiple high-severity repair triggers",
        }
    return {
        "mode": "apply_reversible_repairs",
        "reason": "repair actions are reversible TD3 controls",
    }
