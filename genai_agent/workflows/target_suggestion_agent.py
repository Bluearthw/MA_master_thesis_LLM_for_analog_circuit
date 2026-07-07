import os
import re


def _read_text(path):
    if not path or not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as file:
            return file.read()
    except OSError:
        return ""


def _extract_vdd(netlist_text, fallback=1.2):
    patterns = [
        r"\.param\s+.*?\bVDD_VAL\s*=\s*([0-9.+\-eE]+)",
        r"\.param\s+.*?\bVDD\s*=\s*([0-9.+\-eE]+)",
        r"^\s*vdd\s+\S+\s+\S+\s+dc\s*=?\s*([0-9.+\-eE]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, netlist_text, re.IGNORECASE | re.MULTILINE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    return fallback


def _classify_circuit(targets, netlist_text, context):
    target_names = {str(name).lower() for name in targets}
    text = netlist_text.lower()
    dut_config = context.get("data_for_dut_yaml")
    is_differential = False
    has_input = False
    if isinstance(dut_config, (list, tuple)) and len(dut_config) >= 2:
        is_differential = bool(dut_config[0])
        has_input = bool(dut_config[1])

    if "oscillation_frequency" in target_names:
        return "oscillator"
    if {"line_regulation", "load_regulation", "startup_behavior"} & target_names:
        return "regulator"
    if has_input or "vin1" in text or "iin1" in text:
        return "differential_amplifier" if is_differential else "single_ended_amplifier"
    return "generic"


def _target_value(name, default, circuit_kind, vdd):
    """Return (suggested_value, reason) or (None, None) to keep the default."""
    name = str(name)
    key = name.lower()

    if key == "area":
        return default, "kept generic area limit"

    if key == "current":
        if circuit_kind in {"single_ended_amplifier", "differential_amplifier"}:
            return min(float(default), 1e-3) if float(default) > 0 else 1e-3, "bounded amplifier current target to a practical mA-scale value"
        return default, "kept default current target"

    if circuit_kind in {"single_ended_amplifier", "differential_amplifier"}:
        amplifier_rules = {
            "dc_gain": (10.0, "baseline voltage-gain requirement for generated amplifier topologies"),
            "bandwidth": (1e6, "replaced very low generic bandwidth with a MHz-scale amplifier sanity target"),
            "gain_margin": (45.0, "standard stability margin target"),
            "phase_margin": (60.0, "standard stability margin target"),
            "psrr": (10.0, "baseline supply-rejection requirement"),
            "input_total_noise": (1e-4, "relaxed generic low-noise target for simple generated input stages"),
            "output_total_noise": (3e-4, "relaxed generic low-noise target for simple generated output stages"),
            "slew_rate": (1.0, "baseline slew-rate target for initial RL sizing"),
            "ugbw": (1e6, "baseline unity-gain bandwidth target"),
            "cmrr": (20.0, "baseline common-mode rejection target"),
            "cm_gain": (-20.0, "baseline common-mode gain target"),
            "dm_gain": (10.0, "baseline differential gain target"),
            "output_balance": (1.0, "kept boolean/pass-style output-balance target"),
        }
        if key in amplifier_rules:
            value, reason = amplifier_rules[key]
            return value, reason

    if circuit_kind == "regulator":
        regulator_rules = {
            "dc_output_voltage": (0.5 * vdd, "set output target near mid-supply when no explicit requirement is available"),
            "line_regulation": (5.0, "baseline generated-regulator line-regulation target"),
            "load_regulation": (5.0, "baseline generated-regulator load-regulation target"),
            "output_total_noise": (1e-4, "baseline generated-regulator output-noise target"),
            "psrr": (20.0, "baseline generated-regulator PSRR target"),
            "startup_behavior": (2.0, "kept generic startup-time target"),
            "temperature_coefficient": (800.0, "kept generic temperature-coefficient target"),
        }
        if key in regulator_rules:
            value, reason = regulator_rules[key]
            return value, reason

    return default, "kept global default"


def suggest_target_values(targets, context=None):
    """Suggest circuit-aware target values before user review.

    This is intentionally deterministic: it behaves like a local agent with a
    stable interface, so the YAML path does not depend on an LLM call.
    """
    context = context or {}
    netlist_text = context.get("netlist_text") or _read_text(context.get("netlist_path"))
    vdd = _extract_vdd(netlist_text)
    circuit_kind = _classify_circuit(targets, netlist_text, context)

    suggested = {}
    reasons = {}
    for name, default in targets.items():
        try:
            default_value = float(default)
        except (TypeError, ValueError):
            default_value = 0.0
        value, reason = _target_value(name, default_value, circuit_kind, vdd)
        suggested[name] = float(value)
        reasons[name] = reason

    return {
        "targets": suggested,
        "reasons": reasons,
        "circuit_kind": circuit_kind,
        "vdd": vdd,
    }


def print_suggestions(suggestion):
    print("\n=== Target Suggestion Agent ===")
    print(f"Detected circuit kind: {suggestion.get('circuit_kind', 'generic')}")
    print(f"Detected/assumed VDD: {suggestion.get('vdd', 1.2)}")
    for name, value in sorted(suggestion.get("targets", {}).items()):
        reason = suggestion.get("reasons", {}).get(name, "")
        print(f"  {name}: {value}  # {reason}")
