import json
import math
from pathlib import Path


def curriculum_target_path(circuit_name, dataset_root="material/dataset"):
    circuit_name = str(circuit_name)
    return Path(dataset_root) / circuit_name / "curriculum_targets.json"


def _is_finite_number(value):
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _is_met(metric_name, measured_value, official_target, list_min_targets):
    if not _is_finite_number(measured_value) or not _is_finite_number(official_target):
        return False
    measured = float(measured_value)
    target = float(official_target)
    if metric_name in set(list_min_targets or []):
        return measured <= target
    return measured >= target


def _loose_target(metric_name, official_target, list_min_targets):
    target = float(official_target)
    if metric_name in set(list_min_targets or []):
        return 1.1 * target
    return 0.9 * target


def build_curriculum_targets(circuit_name, run_id, official_targets, best_specs, list_min_targets, best_constraints_met=False):
    targets = {}
    best_specs = best_specs or {}
    official_targets = official_targets or {}

    for metric_name, official_target in official_targets.items():
        if not _is_finite_number(official_target):
            continue

        best_measured = best_specs.get(metric_name)
        is_met = _is_met(metric_name, best_measured, official_target, list_min_targets)
        if is_met:
            curriculum_target = float(best_measured)
        else:
            curriculum_target = _loose_target(metric_name, official_target, list_min_targets)

        targets[str(metric_name)] = {
            "official_target": float(official_target),
            "best_measured": float(best_measured) if _is_finite_number(best_measured) else None,
            "is_met": bool(is_met),
            "curriculum_target": float(curriculum_target),
        }

    return {
        "circuit_name": str(circuit_name),
        "source_run_id": str(run_id),
        "best_constraints_met": bool(best_constraints_met),
        "targets": targets,
    }


def save_curriculum_targets(circuit_name, run_id, official_targets, best_specs, list_min_targets, best_constraints_met=False):
    data = build_curriculum_targets(
        circuit_name,
        run_id,
        official_targets,
        best_specs,
        list_min_targets,
        best_constraints_met=best_constraints_met,
    )
    path = curriculum_target_path(circuit_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, allow_nan=False)
    return path


def load_curriculum_target_values(circuit_name):
    path = curriculum_target_path(circuit_name)
    if not path.is_file():
        return None
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    values = {}
    for metric_name, metric_data in data.get("targets", {}).items():
        value = metric_data.get("curriculum_target")
        if _is_finite_number(value):
            values[str(metric_name)] = float(value)
    return values
