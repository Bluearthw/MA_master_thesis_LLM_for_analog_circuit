import json
import os
import re
from datetime import datetime
from pathlib import Path

import yaml

from utils import gen_utils


ADAPTER_VERSION = 1
REQUIRED_ADAPTER_FIELDS = (
    "version",
    "created_at",
    "circuit_id",
    "category",
    "topology_subtype",
    "device_roles",
    "matched_groups",
    "action_groups",
    "initial_action_mask",
    "parameter_bound_overrides",
    "dc_feasibility_terms",
    "spec_to_action_hints",
    "memory_retrieval_keys",
    "confidence",
    "evidence",
)


def load_yaml_config(circuit_id, yaml_dir=None):
    yaml_dir = Path(yaml_dir or Path("ngspice_interface") / "files" / "yaml_files")
    yaml_path = yaml_dir / f"{circuit_id}.yaml"
    with open(yaml_path, "r", encoding="utf-8") as file:
        return yaml.load(file, Loader=yaml.Loader), yaml_path


def find_netlist_path(circuit_id):
    candidates = [
        Path("genai_agent") / "output" / str(circuit_id) / "final_netlist.cir",
        Path("no_backup") / "output_netlists" / f"{circuit_id}.cir",
        Path("ngspice_interface") / "files" / "input_netlists" / f"{circuit_id}.cir",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def parse_netlist_devices(netlist_text):
    devices = {}
    for line in netlist_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("*") or stripped.startswith("."):
            continue
        parts = stripped.split()
        name = parts[0]
        prefix = name[:1].lower()
        if prefix not in {"m", "c", "r", "v", "i"}:
            continue
        devices[name] = {
            "line": stripped,
            "kind": _device_kind(prefix, parts),
            "nodes": parts[1:5] if prefix == "m" and len(parts) >= 5 else parts[1:3],
        }
    return devices


def _device_kind(prefix, parts):
    if prefix == "m" and len(parts) >= 6:
        model = parts[5].lower()
        if "pmos" in model:
            return "pmos"
        if "nmos" in model:
            return "nmos"
        return "mos"
    return {
        "c": "capacitor",
        "r": "resistor",
        "v": "voltage_source",
        "i": "current_source",
    }.get(prefix, "unknown")


def infer_device_roles(devices):
    roles = {}
    for name, data in devices.items():
        kind = data["kind"]
        line = data["line"]
        if kind == "nmos":
            role = "input_or_gain_device" if re.search(r"\bVIN", line, re.IGNORECASE) else "nmos_device"
        elif kind == "pmos":
            role = "active_load_or_bias_device"
        elif kind == "capacitor":
            role = "load_or_compensation_capacitor"
        elif kind == "voltage_source":
            role = "input_source" if re.search(r"\bVIN", name, re.IGNORECASE) else "bias_or_supply_source"
        else:
            role = kind
        roles[name] = {
            "role": role,
            "device_kind": kind,
            "evidence": line,
        }
    return roles


def infer_action_groups(param_names):
    groups = []
    used = set()
    suffixes = sorted({name[1:] for name in param_names if len(name) > 1 and name[0] in {"w", "l", "m"}})
    for suffix in suffixes:
        members = [name for name in (f"w{suffix}", f"l{suffix}", f"m{suffix}") if name in param_names]
        if members:
            groups.append(
                {
                    "name": f"device_{suffix}_sizing",
                    "role_hint": "transistor_sizing",
                    "parameters": members,
                    "canonical_slot": _canonical_slot_for_suffix(suffix),
                    "active": True,
                    "evidence": f"Grouped width/length/multiplier parameters sharing suffix '{suffix}'.",
                }
            )
            used.update(members)

    for name in param_names:
        if name in used:
            continue
        groups.append(
            {
                "name": f"{name}_control",
                "role_hint": _role_hint_for_param(name),
                "parameters": [name],
                "canonical_slot": _canonical_slot_for_param(name),
                "active": True,
                "evidence": f"Single optimizable parameter '{name}' from YAML.",
            }
        )
    return groups


def _canonical_slot_for_suffix(suffix):
    if suffix.startswith("n"):
        return "nmos_input_or_gain_device"
    if suffix.startswith("p"):
        return "pmos_load_or_output_device"
    return "device_sizing"


def _role_hint_for_param(name):
    lowered = name.lower()
    if "bias" in lowered or lowered.startswith("vb"):
        return "bias_control"
    if lowered.startswith("c"):
        return "capacitive_load_or_compensation"
    if lowered.startswith("r"):
        return "resistive_load_or_feedback"
    return "unclassified_parameter"


def _canonical_slot_for_param(name):
    lowered = name.lower()
    if "vin" in lowered and "bias" in lowered:
        return "input_bias"
    if lowered.startswith("vb"):
        return "bias_voltage"
    if lowered.startswith("c"):
        return "load_or_compensation_capacitor"
    if lowered.startswith("r"):
        return "resistor"
    return "misc_parameter"


def infer_topology_subtype(devices, targets):
    kinds = [item["kind"] for item in devices.values()]
    has_one_nmos = kinds.count("nmos") == 1
    has_one_pmos = kinds.count("pmos") == 1
    has_gain_targets = "dc_gain" in targets and "bandwidth" in targets
    if has_one_nmos and has_one_pmos and has_gain_targets:
        return "single_ended_common_source_with_active_load"
    if has_gain_targets:
        return "single_ended_amplifier_unknown_subtype"
    return "unknown"


def build_adapter(circuit_id, category=None, yaml_dir=None):
    yaml_data, yaml_path = load_yaml_config(circuit_id, yaml_dir=yaml_dir)
    netlist_path = find_netlist_path(circuit_id)
    netlist_text = netlist_path.read_text(encoding="utf-8") if netlist_path else ""
    devices = parse_netlist_devices(netlist_text)
    param_names = list(yaml_data.get("params", {}).keys())
    targets = list(yaml_data.get("targets", {}).keys())
    hard_constraints = list(yaml_data.get("hard_constraints", []))
    optimization_targets = list(yaml_data.get("optimization_targets", []))
    category_key = category or f"category_{gen_utils.find_cat_from_num(circuit_id)}"
    action_groups = infer_action_groups(param_names)

    adapter = {
        "version": ADAPTER_VERSION,
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "circuit_id": str(circuit_id),
        "category": category_key,
        "topology_subtype": infer_topology_subtype(devices, targets),
        "device_roles": infer_device_roles(devices),
        "matched_groups": infer_matched_groups(action_groups),
        "action_groups": action_groups,
        "initial_action_mask": [
            {"parameter": name, "active": True, "reason": "Phase-1 adapter keeps all YAML parameters active."}
            for name in param_names
        ],
        "parameter_bound_overrides": {},
        "dc_feasibility_terms": infer_dc_feasibility_terms(targets, hard_constraints),
        "spec_to_action_hints": infer_spec_to_action_hints(targets, action_groups),
        "memory_retrieval_keys": [
            category_key,
            infer_topology_subtype(devices, targets),
            f"targets:{','.join(targets)}",
        ],
        "confidence": {
            "overall": 0.45 if netlist_path else 0.25,
            "reason": "Deterministic Phase-1 adapter from YAML/netlist naming heuristics; not yet LLM-reviewed.",
        },
        "evidence": {
            "yaml_path": str(yaml_path),
            "netlist_path": str(netlist_path) if netlist_path else None,
            "param_names": param_names,
            "target_names": targets,
            "hard_constraints": hard_constraints,
            "optimization_targets": optimization_targets,
            "path_ids": {str(key): str(value) for key, value in yaml_data.get("path_id", {}).items()},
            "dut_config": yaml_data.get("dut_config", {}),
        },
    }
    return adapter


def infer_matched_groups(action_groups):
    # Phase 1 is conservative: no matched groups are asserted without explicit evidence.
    return [
        {
            "name": "no_asserted_matching_groups",
            "members": [],
            "reason": "No deterministic matching evidence in YAML-only adapter.",
            "active": False,
        }
    ]


def infer_dc_feasibility_terms(targets, hard_constraints):
    terms = [
        {
            "name": "simulation_converged",
            "source": "ngspice_status",
            "direction": "must_pass",
            "reason": "Reject failed simulations before full-spec reward interpretation.",
        },
        {
            "name": "op_alive_ratio",
            "source": "op_device_metrics",
            "direction": "maximize",
            "reason": "Cheap OP proxy for whether devices are conducting.",
        },
        {
            "name": "op_saturation_ratio",
            "source": "op_device_metrics",
            "direction": "maximize",
            "reason": "Cheap OP proxy for analog bias validity.",
        },
    ]
    if "current" in targets:
        terms.append(
            {
                "name": "supply_current_sanity",
                "source": "current_metric",
                "direction": "bounded",
                "reason": "Avoid dead circuits and obviously excessive current before expensive evaluation.",
            }
        )
    if "dc_gain" in hard_constraints:
        terms.append(
            {
                "name": "low_fidelity_dc_gain",
                "source": "ac_or_op_ac_measurement",
                "direction": "maximize",
                "reason": "Gain is a hard constraint and a useful early proxy for amplifier viability.",
            }
        )
    return terms


def infer_spec_to_action_hints(targets, action_groups):
    group_names = [group["name"] for group in action_groups]
    hints = []
    for target in targets:
        relevant = []
        if target in {"dc_gain", "bandwidth", "psrr", "slew_rate"}:
            relevant = [name for name in group_names if "device_" in name or "bias" in name.lower()]
        elif target in {"area", "current", "input_total_noise"}:
            relevant = group_names
        hints.append(
            {
                "spec": target,
                "candidate_action_groups": relevant,
                "confidence": 0.35,
                "reason": "Phase-1 heuristic hint; should be replaced or confirmed by LLM adapter evidence.",
            }
        )
    return hints


def assert_adapter_shape(adapter):
    missing = [field for field in REQUIRED_ADAPTER_FIELDS if field not in adapter]
    if missing:
        raise ValueError(f"Adapter is missing required fields: {missing}")
    if adapter["version"] != ADAPTER_VERSION:
        raise ValueError(f"Unsupported adapter version: {adapter['version']}")
    if not isinstance(adapter["action_groups"], list):
        raise TypeError("adapter['action_groups'] must be a list")
    if not isinstance(adapter["initial_action_mask"], list):
        raise TypeError("adapter['initial_action_mask'] must be a list")
    return True


def default_adapter_path(circuit_id, category=None, base_dir=None):
    category_key = category or f"category_{gen_utils.find_cat_from_num(circuit_id)}"
    base = Path(base_dir or Path("solutions") / "category_memory" / "adapters")
    return base / category_key / f"{circuit_id}_adapter.json"


def save_adapter(adapter, path=None):
    assert_adapter_shape(adapter)
    output_path = Path(path or default_adapter_path(adapter["circuit_id"], adapter["category"]))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(adapter, file, indent=2, sort_keys=True, allow_nan=False)
    return output_path


def load_adapter(path):
    with open(path, "r", encoding="utf-8") as file:
        adapter = json.load(file)
    assert_adapter_shape(adapter)
    return adapter


def inspect_adapter(adapter):
    assert_adapter_shape(adapter)
    return {
        "circuit_id": adapter["circuit_id"],
        "category": adapter["category"],
        "topology_subtype": adapter["topology_subtype"],
        "action_group_count": len(adapter["action_groups"]),
        "active_parameter_count": sum(1 for item in adapter["initial_action_mask"] if item.get("active")),
        "dc_feasibility_terms": [item["name"] for item in adapter["dc_feasibility_terms"]],
        "memory_retrieval_keys": list(adapter["memory_retrieval_keys"]),
    }

