import json
from pathlib import Path

from .adapter import build_adapter, validate_adapter
from .category_memory import iter_records


def build_transfer_plan(adapter, max_records=20, memory_dir=None):
    validation = validate_adapter(adapter)
    plan = {
        "circuit_id": adapter.get("circuit_id"),
        "category": adapter.get("category"),
        "adapter_valid": bool(validation["valid"]),
        "validation": validation,
        "memory_records_used": [],
        "memory_records_rejected": [],
        "warm_start_candidates": [],
        "replay_seed_policy": "none",
        "weight_transfer_policy": "none",
        "low_fidelity_policy": "pretrain",
        "fallback_policy": {
            "on_invalid_adapter": "fallback_to_v1_or_plain_td3",
            "on_negative_transfer": "drop_replay_then_disable_masks_then_plain_td3",
        },
    }

    if not validation["valid"]:
        plan["low_fidelity_policy"] = "skip"
        return plan

    adapter_param_names = set(adapter["evidence"].get("param_names", []))
    adapter_targets = set(adapter["evidence"].get("target_names", []))
    adapter_slots = {group.get("canonical_slot") for group in adapter.get("action_groups", []) if group.get("canonical_slot")}

    records = list(iter_records(adapter["category"], memory_dir) or [])
    records.sort(key=lambda item: float(item.get("reward", float("-inf"))), reverse=True)

    for record in records[: max(0, int(max_records))]:
        decision = score_memory_record(record, adapter_param_names, adapter_targets, adapter_slots)
        if decision["usable"]:
            plan["memory_records_used"].append(decision)
            plan["warm_start_candidates"].append(
                {
                    "source_circuit": str(record.get("circuit_name")),
                    "reward": record.get("reward"),
                    "constraints_met": record.get("constraints_met"),
                    "params": record.get("params", {}),
                    "reason": decision["reason"],
                }
            )
        else:
            plan["memory_records_rejected"].append(decision)

    if plan["warm_start_candidates"]:
        plan["replay_seed_policy"] = "points_only"
        plan["low_fidelity_policy"] = "probe"
    elif records:
        plan["low_fidelity_policy"] = "probe"
    else:
        plan["low_fidelity_policy"] = "pretrain"

    plan["weight_transfer_policy"] = "none"
    return plan


def score_memory_record(record, adapter_param_names, adapter_targets, adapter_slots):
    record_params = set(record.get("param_names", []))
    record_targets = set(record.get("target_signature", {}).get("targets", []))
    target_overlap = sorted(adapter_targets & record_targets)
    param_overlap = sorted(adapter_param_names & record_params)
    target_jaccard = _jaccard(adapter_targets, record_targets)
    param_jaccard = _jaccard(adapter_param_names, record_params)

    exact_params = record_params == adapter_param_names
    exact_targets = record_targets == adapter_targets
    exact_dims = (
        int(record.get("action_dim", -1)) == len(adapter_param_names)
        and int(record.get("state_dim", -1)) == len(adapter_targets)
    )
    usable = bool(exact_params and exact_targets and exact_dims)

    if usable:
        reason = "Exact param/target/dimension compatibility; safe for candidate warm-start."
    else:
        reason = "Rejected for direct replay/point transfer: "
        causes = []
        if not exact_params:
            causes.append(f"parameter mismatch overlap={len(param_overlap)}/{len(adapter_param_names)}")
        if not exact_targets:
            causes.append(f"target mismatch overlap={len(target_overlap)}/{len(adapter_targets)}")
        if not exact_dims:
            causes.append("state/action dimension mismatch")
        reason += "; ".join(causes)

    return {
        "usable": usable,
        "source_circuit": str(record.get("circuit_name")),
        "source_run_id": record.get("run_id"),
        "reward": record.get("reward"),
        "constraints_met": record.get("constraints_met"),
        "target_overlap": target_overlap,
        "param_overlap": param_overlap,
        "target_jaccard": target_jaccard,
        "param_jaccard": param_jaccard,
        "adapter_canonical_slots": sorted(slot for slot in adapter_slots if slot),
        "record_param_names": sorted(record_params),
        "reason": reason,
    }


def _jaccard(left, right):
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 0.0
    return float(len(left & right) / len(union))


def build_transfer_plan_for_circuit(circuit_id, category=None, max_records=20, memory_dir=None):
    adapter = build_adapter(circuit_id, category=category)
    return build_transfer_plan(adapter, max_records=max_records, memory_dir=memory_dir)


def save_transfer_plan(plan, path):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(plan, file, indent=2, sort_keys=True, allow_nan=False)
    return output_path

