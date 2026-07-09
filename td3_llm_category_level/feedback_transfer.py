import json
import os
from collections import Counter, defaultdict
from pathlib import Path

from .feedback import default_feedback_dir


def iter_feedback_paths(category=None, feedback_dir=None):
    base_dir = Path(feedback_dir) if feedback_dir else default_feedback_dir()
    if category:
        base_dir = base_dir / str(category)
    if not base_dir.exists():
        return
    yield from base_dir.rglob("*_feedback.json")


def load_feedback_summary(path):
    with open(path, "r", encoding="utf-8") as feedback_file:
        return json.load(feedback_file)


def load_feedback_summaries(category=None, feedback_dir=None, exclude_circuit=None, max_summaries=20):
    summaries = []
    for path in iter_feedback_paths(category=category, feedback_dir=feedback_dir) or []:
        summary = load_feedback_summary(path)
        if exclude_circuit is not None and str(summary.get("circuit_name")) == str(exclude_circuit):
            continue
        summary["_feedback_path"] = str(path)
        summaries.append(summary)

    summaries.sort(key=lambda item: str(item.get("saved_at", "")), reverse=True)
    return summaries[: max(0, int(max_summaries))]


def build_feedback_transfer_plan(
    circuit_id,
    category,
    base_transfer_plan=None,
    feedback_dir=None,
    max_summaries=20,
):
    summaries = load_feedback_summaries(
        category=category,
        feedback_dir=feedback_dir,
        exclude_circuit=circuit_id,
        max_summaries=max_summaries,
    )
    recommendation_counts = Counter()
    spec_priority_counts = Counter()
    boundary_counts = Counter()
    low_fidelity_verdicts = Counter()
    memory_verdicts = Counter()
    evidence = []

    for summary in summaries:
        evidence.append(
            {
                "run_id": summary.get("run_id"),
                "circuit_name": summary.get("circuit_name"),
                "feedback_path": summary.get("_feedback_path"),
                "strict_pass": summary.get("strict_pass"),
                "best_reward": summary.get("best_reward"),
            }
        )
        low_fidelity_verdicts[summary.get("low_fidelity_analysis", {}).get("verdict", "unknown")] += 1
        memory_verdicts[summary.get("memory_transfer_analysis", {}).get("verdict", "unknown")] += 1
        for recommendation in summary.get("recommendations", []):
            recommendation_type = recommendation.get("type")
            if recommendation_type:
                recommendation_counts[recommendation_type] += 1
            if recommendation_type == "increase_spec_priority" and recommendation.get("target"):
                spec_priority_counts[recommendation["target"]] += 1
            if recommendation.get("param"):
                boundary_counts[recommendation["param"]] += 1

    low_fidelity_policy = _choose_feedback_low_fidelity_policy(low_fidelity_verdicts, summaries)
    memory_policy = _choose_memory_policy(memory_verdicts, summaries)
    exploration_policy = _choose_exploration_policy(recommendation_counts)

    plan = {
        "circuit_id": str(circuit_id),
        "category": str(category),
        "source": "category_feedback",
        "feedback_summaries_used": evidence,
        "feedback_summaries_used_count": len(summaries),
        "recommendation_counts": dict(recommendation_counts),
        "low_fidelity_verdicts": dict(low_fidelity_verdicts),
        "memory_verdicts": dict(memory_verdicts),
        "low_fidelity_policy_override": low_fidelity_policy,
        "memory_policy": memory_policy,
        "exploration_policy": exploration_policy,
        "reward_weight_hints": [
            {"target": target, "reason": "frequently failed in previous category traces"}
            for target, _ in spec_priority_counts.most_common()
        ],
        "boundary_hints": [
            {"param": param, "reason": "previous top candidates clustered at boundary"}
            for param, _ in boundary_counts.most_common()
        ],
        "applied_controls": [],
        "fallback_policy": {
            "on_no_feedback": "use_adapter_transfer_plan",
            "on_negative_transfer": "reduce_memory_then_skip_low_fidelity_then_baseline_td3",
        },
    }

    if base_transfer_plan:
        plan["base_adapter_valid"] = bool(base_transfer_plan.get("adapter_valid", False))
        plan["base_memory_records_used"] = len(base_transfer_plan.get("memory_records_used", []))
        plan["base_memory_records_rejected"] = len(base_transfer_plan.get("memory_records_rejected", []))

    return plan


def apply_feedback_transfer_plan_to_args(args, feedback_plan):
    controls = []
    if not feedback_plan or feedback_plan.get("feedback_summaries_used_count", 0) <= 0:
        return args

    low_fidelity = feedback_plan.get("low_fidelity_policy_override", {})
    mode = low_fidelity.get("mode")
    if mode == "skip":
        args.dc_seed_samples = 0
        args.dc_seed_elites = 0
        args.full_warmup_steps = max(int(getattr(args, "full_warmup_steps", 0) or 0), 10)
        controls.append("skip_low_fidelity")
    elif mode == "probe":
        args.dc_seed_samples = min(int(getattr(args, "dc_seed_samples", 0) or 0), 8)
        args.dc_seed_elites = min(int(getattr(args, "dc_seed_elites", 0) or 0), 2)
        args.full_warmup_steps = max(int(getattr(args, "full_warmup_steps", 0) or 0), 8)
        controls.append("probe_low_fidelity")

    memory_policy = feedback_plan.get("memory_policy", {})
    if memory_policy.get("mode") == "reduce":
        args.warm_start_records = min(int(getattr(args, "warm_start_records", 0) or 0), 5)
        controls.append("reduce_memory_records")

    exploration_policy = feedback_plan.get("exploration_policy", {})
    if exploration_policy.get("mode") == "increase":
        args.noise_sigma = max(float(getattr(args, "noise_sigma", 0.1)), 0.2)
        controls.append("increase_noise_sigma")

    feedback_plan["applied_controls"] = controls
    return args


def save_feedback_transfer_plan(plan, path):
    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_suffix(target_path.suffix + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as plan_file:
        json.dump(plan, plan_file, indent=2, allow_nan=False)
    os.replace(temp_path, target_path)
    return target_path


def _choose_feedback_low_fidelity_policy(verdicts, summaries):
    if not summaries:
        return {
            "mode": "no_override",
            "reason": "no previous category feedback summaries",
        }
    if verdicts.get("costly_uncertain", 0) >= max(1, len(summaries) // 2):
        return {
            "mode": "skip",
            "reason": "previous traces show low-fidelity cost without strict-pass evidence",
        }
    if verdicts.get("helpful", 0) > 0:
        return {
            "mode": "probe",
            "reason": "previous traces contain useful low-fidelity evidence; keep budget small",
        }
    return {
        "mode": "probe",
        "reason": "previous traces are inconclusive; collect small OP/DC probe only",
    }


def _choose_memory_policy(verdicts, summaries):
    if not summaries:
        return {"mode": "default", "reason": "no feedback evidence"}
    if verdicts.get("possible_negative_transfer", 0) >= max(1, len(summaries) // 2):
        return {
            "mode": "reduce",
            "reason": "previous memory-assisted traces often stagnated",
        }
    return {
        "mode": "default",
        "reason": "no dominant negative-transfer evidence",
    }


def _choose_exploration_policy(recommendation_counts):
    if recommendation_counts.get("increase_exploration", 0) > 0:
        return {
            "mode": "increase",
            "reason": "previous traces recommend higher exploration",
        }
    return {
        "mode": "default",
        "reason": "no exploration change recommended",
    }
