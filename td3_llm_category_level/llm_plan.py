import json
import os
from pathlib import Path


ALLOWED_ACTIONS = {
    "increase_exploration",
    "reduce_memory_transfer",
    "switch_low_fidelity",
    "increase_spec_priority",
    "unbias_boundary_param",
    "fallback_to_baseline",
}

ALLOWED_LOW_FIDELITY_MODES = {"skip", "probe", "gate", "pretrain", "no_override"}


def validate_llm_planner_output(plan, adapter=None, known_targets=None):
    errors = []
    warnings = []
    if not isinstance(plan, dict):
        return {"valid": False, "errors": ["plan must be a dictionary"], "warnings": []}

    actions = plan.get("actions", [])
    if not isinstance(actions, list):
        errors.append("actions must be a list")
        actions = []

    known_params = set()
    if adapter:
        known_params.update(adapter.get("evidence", {}).get("param_names", []) or [])
        for group in adapter.get("action_groups", []) or []:
            known_params.update(group.get("params", []) or [])
    known_targets = set(known_targets or (adapter or {}).get("evidence", {}).get("target_names", []) or [])

    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            errors.append(f"actions[{index}] must be a dictionary")
            continue
        action_type = action.get("type")
        if action_type not in ALLOWED_ACTIONS:
            errors.append(f"actions[{index}].type is not allowed: {action_type}")

        controls = action.get("controls", {}) or {}
        if not isinstance(controls, dict):
            errors.append(f"actions[{index}].controls must be a dictionary")
            continue

        if "param" in controls and known_params and controls["param"] not in known_params:
            errors.append(f"actions[{index}] references unknown param: {controls['param']}")
        if "target" in controls and known_targets and controls["target"] not in known_targets:
            errors.append(f"actions[{index}] references unknown target: {controls['target']}")
        if action_type == "switch_low_fidelity" and controls.get("mode") not in ALLOWED_LOW_FIDELITY_MODES:
            errors.append(f"actions[{index}] has invalid low-fidelity mode: {controls.get('mode')}")
        if action_type == "increase_exploration":
            sigma = controls.get("noise_sigma_min")
            if sigma is not None and (not _is_number(sigma) or float(sigma) <= 0.0):
                errors.append(f"actions[{index}] has invalid noise_sigma_min: {sigma}")

    if plan.get("relax_final_targets"):
        errors.append("LLM plan must not relax final targets")
    if plan.get("direct_td3_actions"):
        errors.append("LLM plan must not provide direct TD3 action vectors")
    if not actions:
        warnings.append("plan contains no actions")

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def save_llm_plan_validation(validation, path):
    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_suffix(target_path.suffix + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as validation_file:
        json.dump(validation, validation_file, indent=2, allow_nan=False)
    os.replace(temp_path, target_path)
    return target_path


def _is_number(value):
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False
