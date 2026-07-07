import re


LOOP_HINT_PATTERNS = [
    r"\bstb\b",
    r"\bloop[_\s-]?gain\b",
    r"\breturn[_\s-]?ratio\b",
    r"\biprobe\b",
    r"\bvprobe\b",
    r"\bvloop\b",
    r"\bstability\b",
]

REGULATOR_HINT_PATTERNS = [
    r"\bregulator\b",
    r"\bldo\b",
    r"\bbandgap\b",
    r"\bvref\b",
    r"\bvfb\b",
    r"\bfeedback\b",
    r"\bline[_\s-]?regulation\b",
    r"\bload[_\s-]?regulation\b",
]

OSCILLATOR_HINT_PATTERNS = [
    r"\boscillator\b",
    r"\bvco\b",
    r"\bring\b",
    r"\btank\b",
    r"\blc\b",
    r"\btuning\b",
    r"\boscillation\b",
]


def _strip_control_blocks(netlist_text):
    return re.sub(r"(?is)\.control.*?\.endc", "", netlist_text)


def _source_lines(netlist_text):
    body = _strip_control_blocks(netlist_text)
    lines = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("*", ".", "+")):
            continue
        lines.append(line)
    return lines


def _has_any(patterns, text):
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _tokens(line):
    return re.split(r"\s+", line.split(";", 1)[0].split("$", 1)[0].strip())


def extract_features(netlist_text, data_for_dut_yaml=None):
    body_text = _strip_control_blocks(netlist_text)
    full_lower = netlist_text.lower()
    body_lower = body_text.lower()
    lines = _source_lines(netlist_text)

    node_refs = set()
    mos_count = 0
    capacitor_count = 0
    resistor_count = 0
    feedback_edges = []

    for line in lines:
        parts = _tokens(line)
        if not parts:
            continue
        device = parts[0].lower()
        prefix = device[0]
        if prefix == "m" and len(parts) >= 5:
            mos_count += 1
            drain, gate, source, bulk = parts[1:5]
            node_refs.update(node.lower() for node in (drain, gate, source, bulk))
        elif prefix == "c" and len(parts) >= 3:
            capacitor_count += 1
            node_refs.update(node.lower() for node in parts[1:3])
        elif prefix == "r" and len(parts) >= 3:
            resistor_count += 1
            node_refs.update(node.lower() for node in parts[1:3])
            a, b = parts[1].lower(), parts[2].lower()
            if {"vout1", "vout2"} & {a, b} and {"vin1", "vin2", "fb", "vfb"} & {a, b}:
                feedback_edges.append((a, b, parts[0]))
        elif prefix in {"v", "i", "e", "g"} and len(parts) >= 3:
            node_refs.update(node.lower() for node in parts[1:3])

    is_differential_yaml = False
    has_input_yaml = False
    if isinstance(data_for_dut_yaml, (list, tuple)) and len(data_for_dut_yaml) >= 2:
        is_differential_yaml = bool(data_for_dut_yaml[0])
        has_input_yaml = bool(data_for_dut_yaml[1])

    has_vin1 = "vin1" in node_refs or re.search(r"\bVIN1\b", body_text, re.IGNORECASE) is not None
    has_vin2 = "vin2" in node_refs or re.search(r"\bVIN2\b", body_text, re.IGNORECASE) is not None
    has_iin1 = "iin1" in node_refs or re.search(r"\bIIN1\b", body_text, re.IGNORECASE) is not None
    has_vout1 = "vout1" in node_refs or re.search(r"\bVOUT1\b", body_text, re.IGNORECASE) is not None
    has_vout2 = "vout2" in node_refs or re.search(r"\bVOUT2\b", body_text, re.IGNORECASE) is not None

    has_fb_node = bool({"fb", "vfb", "feedback"} & node_refs)
    has_loop_testbench = _has_any(LOOP_HINT_PATTERNS, netlist_text)
    has_feedback_path = bool(feedback_edges) or has_fb_node or _has_any([r"\bfeedback\b", r"\bvfb\b"], body_text)
    has_regulator_hint = _has_any(REGULATOR_HINT_PATTERNS, full_lower) or has_fb_node
    has_oscillator_hint = _has_any(OSCILLATOR_HINT_PATTERNS, full_lower)
    has_transient_stimulus = bool(re.search(r"\b(PULSE|PWL|SIN)\s*\(", body_text, re.IGNORECASE))
    has_psrr_stimulus = bool(re.search(r"alter\s+\w+\s+.*\bac\s*=\s*1", netlist_text, re.IGNORECASE)) and "psrr" in full_lower

    return {
        "has_vin1": has_vin1,
        "has_vin2": has_vin2,
        "has_iin1": has_iin1,
        "has_vout1": has_vout1,
        "has_vout2": has_vout2,
        "has_input": has_input_yaml or has_vin1 or has_iin1,
        "is_differential_input": has_vin1 and has_vin2,
        "is_differential_output": is_differential_yaml or has_vout2,
        "mos_count": mos_count,
        "capacitor_count": capacitor_count,
        "resistor_count": resistor_count,
        "has_loop_testbench": has_loop_testbench,
        "has_feedback_path": has_feedback_path,
        "has_regulator_hint": has_regulator_hint,
        "has_oscillator_hint": has_oscillator_hint,
        "has_transient_stimulus": has_transient_stimulus,
        "has_psrr_stimulus": has_psrr_stimulus,
        "is_simple_open_loop_amp": (
            (has_input_yaml or has_vin1 or has_iin1)
            and has_vout1
            and not has_vout2
            and not has_loop_testbench
            and not has_feedback_path
            and mos_count <= 4
        ),
    }


def _decision(decision, confidence, reason):
    return {
        "decision": decision,
        "confidence": confidence,
        "reason": reason,
    }


def _judge_target(target_id, features):
    target_id = str(target_id)

    if target_id in {"area", "current", "dc_gain", "bandwidth", "input_total_noise", "output_total_noise", "input_impedance", "output_impedance"}:
        return _decision("keep", "high", "General circuit metric.")

    if target_id == "psrr":
        if features["has_psrr_stimulus"]:
            return _decision("keep", "high", "PSRR supply AC stimulus is present.")
        return _decision("questionable", "medium", "PSRR requested but no obvious supply AC injection was detected.")

    if target_id == "slew_rate":
        if features["has_transient_stimulus"]:
            return _decision("keep", "high", "Transient input stimulus is present.")
        return _decision("questionable", "medium", "Slew rate requested but no obvious PULSE/PWL/SIN transient stimulus was detected.")

    if target_id == "gain_margin":
        if features["has_loop_testbench"]:
            return _decision("keep", "high", "Loop/stability testbench evidence is present.")
        if features["is_simple_open_loop_amp"]:
            return _decision("not_applicable", "high", "Simple open-loop one-stage amplifier; gain margin requires loop-gain measurement.")
        return _decision("questionable", "medium", "No loop-gain testbench evidence was detected.")

    if target_id == "phase_margin":
        if features["has_loop_testbench"]:
            return _decision("keep", "high", "Loop/stability testbench evidence is present.")
        if features["is_simple_open_loop_amp"]:
            return _decision("not_applicable", "high", "Simple open-loop one-stage amplifier; phase margin is not a hard stability spec without loop-gain measurement.")
        return _decision("questionable", "medium", "No loop-gain testbench evidence was detected.")

    if target_id in {"cmrr", "dm_gain", "cm_gain", "icmr"}:
        if features["is_differential_input"] or features["is_differential_output"]:
            return _decision("keep", "medium", "Differential input/output evidence is present.")
        return _decision("not_applicable", "high", "Differential/common-mode metric requested for a non-differential circuit.")

    if target_id in {"output_balance", "cmfb_stability"}:
        if features["is_differential_output"]:
            return _decision("keep", "medium", "Differential output evidence is present.")
        return _decision("not_applicable", "high", "Output-balance/CMFB metric requested without differential outputs.")

    if target_id in {"line_regulation", "load_regulation", "startup_behavior", "temperature_coefficient", "output_ripple", "dc_output_voltage"}:
        if features["has_regulator_hint"]:
            return _decision("keep", "medium", "Regulator/reference feedback evidence is present.")
        return _decision("not_applicable", "medium", "Regulator/reference metric requested without regulator topology hints.")

    if target_id in {"oscillation_frequency", "tuning_range_gain"}:
        if features["has_oscillator_hint"]:
            return _decision("keep", "medium", "Oscillator/VCO evidence is present.")
        return _decision("not_applicable", "high", "Oscillator metric requested without oscillator topology hints.")

    return _decision("keep", "low", "No applicability rule exists for this metric.")


def analyze_spec_applicability(struct_path_id, target_id_dict, netlist_text, data_for_dut_yaml=None):
    features = extract_features(netlist_text, data_for_dut_yaml)
    decisions = {}
    keep = {}
    remove = {}
    questionable = {}

    for raw_spec_id, path in struct_path_id.items():
        spec_id = int(raw_spec_id) if isinstance(raw_spec_id, str) and raw_spec_id.isdigit() else raw_spec_id
        target_id = target_id_dict.get(spec_id) or target_id_dict.get(str(spec_id)) or str(spec_id)
        item = _judge_target(target_id, features)
        item.update({"spec_id": spec_id, "target_id": target_id, "path": path})
        decisions[spec_id] = item

        if item["decision"] == "not_applicable" and item["confidence"] == "high":
            remove[spec_id] = item
        elif item["decision"] == "questionable":
            questionable[spec_id] = item
            keep[spec_id] = path
        else:
            keep[spec_id] = path

    return {
        "features": features,
        "decisions": decisions,
        "keep_path_id": keep,
        "removed": remove,
        "questionable": questionable,
    }


def print_report(report):
    removed = report.get("removed", {})
    questionable = report.get("questionable", {})
    print("\n=== Spec Applicability Agent ===")
    features = report.get("features", {})
    print(
        "features:",
        {
            "simple_open_loop_amp": features.get("is_simple_open_loop_amp"),
            "loop_testbench": features.get("has_loop_testbench"),
            "feedback_path": features.get("has_feedback_path"),
            "differential_output": features.get("is_differential_output"),
        },
    )
    if removed:
        print("Removed high-confidence not-applicable specs:")
        for spec_id, item in sorted(removed.items()):
            print(f"  {spec_id} ({item['target_id']}): {item['reason']}")
    if questionable:
        print("Questionable specs kept for user/review:")
        for spec_id, item in sorted(questionable.items()):
            print(f"  {spec_id} ({item['target_id']}): {item['reason']}")
    if not removed and not questionable:
        print("No inapplicable specs detected.")
