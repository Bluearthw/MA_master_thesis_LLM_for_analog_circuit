import re
from genai_agent.data import local_config
from utils import file_utils

DEFAULT_W = "0.5u"
DEFAULT_L = "90n"
DEFAULT_M = "1"
DEFAULT_R = "1k"
DEFAULT_C = "3p"


def match_transistor(match):
    if match:
        transistor_id = match.group(1)
        nodes_and_model = match.group(2)
        try:
            num_id = "".join(re.findall(r"\d+", transistor_id))
        except Exception:
            num_id = transistor_id.replace("M", "_")

        if "nmos" in nodes_and_model.lower():
            prefix = "n"
        elif "pmos" in nodes_and_model.lower():
            prefix = "p"
        else:
            prefix = ""

        w_param = f"w{prefix}{num_id}"
        l_param = f"l{prefix}{num_id}"
        m_param = f"m{prefix}{num_id}"

        param_line = (
            f".param {w_param}={DEFAULT_W} {l_param}={DEFAULT_L} {m_param}={DEFAULT_M}"
        )

        new_transistor_id = f"m{prefix}{num_id}"
        new_m_line = (
            f"{new_transistor_id} {nodes_and_model} w={w_param} l={l_param} m={m_param}"
        )
        return new_m_line, num_id, param_line


def match_RC(match, digit_extractor):
    if match:
        component_id = match.group(1)
        node1 = match.group(2)
        node2 = match.group(3)
        num_id_list = digit_extractor.findall(component_id)
        param_identifier = (
            "".join(num_id_list)
            if num_id_list
            else component_id.replace(component_id[0], "_")
        )

        component_type = component_id[0].lower()
        param_name = f"{component_type}{param_identifier}"
        default_value = DEFAULT_R if component_type == "r" else DEFAULT_C
        param_line = f".param {param_name}={default_value}"
        new_rc_line = f"{component_id} {node1} {node2} {{{param_name}}}"
        return new_rc_line, param_line, param_identifier, component_type


def add_params(netlist):
    param_statements = []
    modified_lines = []
    transistor_ids = []
    resistor_ids_processed = set()
    capacitor_ids_processed = set()
    m_line_pattern = re.compile(r"^(M\S+)\s+(.+?)$", re.IGNORECASE)
    rc_line_pattern = re.compile(r"^([RC]\S+)\s+(\S+)\s+(\S+)$", re.IGNORECASE)
    digit_extractor = re.compile(r"\d+")
    lines = netlist.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line or line.startswith("*") or line.startswith("."):
            modified_lines.append(line)
            continue
        if line.upper().startswith("M"):
            match = m_line_pattern.match(line)
            line, num_id, param_line = match_transistor(match)
            if num_id not in transistor_ids:
                param_statements.append(param_line)
                transistor_ids.append(num_id)
        elif line.upper().startswith(("R", "C")):
            match = rc_line_pattern.match(line)
            if match:
                line, param_line, param_identifier, component_type = match_RC(
                    match, digit_extractor
                )
                is_unique = False
                if component_type == "r" and param_identifier not in resistor_ids_processed:
                    resistor_ids_processed.add(param_identifier)
                    is_unique = True
                elif (
                    component_type == "c"
                    and param_identifier not in capacitor_ids_processed
                ):
                    capacitor_ids_processed.add(param_identifier)
                    is_unique = True
                if is_unique:
                    param_statements.append(param_line)
        modified_lines.append(line)

    param_tran_line = [".param trf=0.5u ; for slew-rate calculation", ".param period=10u "]
    output = ["*params "]
    output.extend(param_statements)
    output.extend(param_tran_line)
    output.extend(modified_lines)
    return "\n".join(output)


def add_DC_source(netlist, vdd="1.2", vb1="0.7", ib1="0.01"):
    param_line = f"\n.param VDD_VAL={vdd}"
    param_line_vb1 = f"\n.param VB1_VAL={vb1}"
    param_line_ib1 = f"\n.param IB1_VAL={ib1}"

    vdd_source = "\nvdd VDD 0 dc=VDD_VAL"
    vss_source = "\nvss VSS 0 dc=0"
    vb1_source = "\nvb1 VB1 0 dc=VB1_VAL"
    ib1_source = "\nib1 IB1 0 dc=IB1_VAL"

    vdd_in_use = re.search(r"\bVDD\b", netlist, re.IGNORECASE)
    vss_in_use = re.search(r"\bVSS\b", netlist, re.IGNORECASE)
    vb_in_use = re.search(r"\bVB1\b", netlist, re.IGNORECASE)
    ib_in_use = re.search(r"\bIB1\b", netlist, re.IGNORECASE)

    insertion_point = 0
    for i, line in enumerate(netlist.splitlines()):
        line_stripped = line.strip()
        if line_stripped and (line_stripped[0].isalpha() or line_stripped.startswith(".")):
            insertion_point = i
            break

    lines = netlist.splitlines()
    if vdd_in_use:
        lines.insert(insertion_point, param_line)
        lines.insert(len(lines), vdd_source)
    if ib_in_use:
        lines.insert(insertion_point, param_line_ib1)
        lines.insert(len(lines), ib1_source)
    if vb_in_use:
        lines.insert(insertion_point, param_line_vb1)
        lines.insert(len(lines), vb1_source)
    if vss_in_use:
        lines.insert(len(lines), vss_source)
    else:
        return netlist

    return "\n".join(lines)


def add_C_load(netlist, node="VOUT1", Cload="10p"):
    param_line = f"\n.param Cload={Cload}"
    cload_line = f"\nCload {node} VSS {{Cload}}"
    lines = netlist.strip().splitlines()
    lines.insert(2, param_line)
    lines.insert(len(lines), cload_line)
    return "\n".join(lines)


def add_OP_simulation(netlist, node="vin1", VINCM="0.6"):
    param_line = f"\n.param VINCM={VINCM}"
    vincm_line = f"\nVicm {node} VSS dc=VINCM"
    op_sim_block = """
.control

option numdgt=4
set temp=25
op
.endc
.end
"""
    lines = netlist.strip().splitlines()
    lines.insert(2, param_line)
    lines.insert(len(lines), vincm_line)
    lines.insert(len(lines), op_sim_block)
    return "\n".join(lines)


def add_AC_simulation(netlist, node="VIN1"):
    VinDM_line = f"\nVinDM {node} VSS dc=0 ac = 1"
    sim_block = """
.control

option numdgt=4
set temp=25
ac dec 10 1 1G
.endc
.end
"""
    lines = netlist.strip().splitlines()
    lines.insert(len(lines), VinDM_line)
    lines.insert(len(lines), sim_block)
    lines.insert(0, "* title line\n")
    return "\n".join(lines)


def add_control(netlist):
    control_block = """
.control

option numdgt=7
set temp=25
set units=degrees
set wr_vecnames 

.endc
.end
"""
    lines = netlist.strip().splitlines()
    lines.insert(len(lines), control_block)
    lines.insert(0, "* title line\n")
    return "\n".join(lines)


def clean_netlist(netlist):
    netlist = netlist.strip()
    netlist = re.sub(r"[()]", "", netlist)
    netlist = re.sub(r"\bnmos4\b", "nmos", netlist)
    netlist = re.sub(r"\bpmos4\b", "pmos", netlist)
    netlist = re.sub(r"\s*resistor\s*", "\n", netlist, flags=re.IGNORECASE)
    netlist = re.sub(r"\s*capacitor\s*", "\n", netlist, flags=re.IGNORECASE)
    return local_config.str_nl_include + netlist


def clean_before_CMFB(netlist):
    lines = netlist.strip().splitlines()
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('set'):
            start_idx = i
        elif stripped == '.endc':
            end_idx = i
            break
    if start_idx is not None and end_idx is not None and start_idx < end_idx:
        new_lines = lines[:start_idx + 1] + lines[end_idx:]
        return '\n'.join(new_lines)
    return netlist


def modify_duplicate_component(circuit_string):
    seen_names = set()
    new_lines = []
    for line in circuit_string.strip().splitlines():
        parts = line.split()
        if not parts:
            new_lines.append(line)
            continue
        designator = parts[0]
        original_name = designator
        counter = 0
        isChanged = False
        while designator in seen_names:
            designator = f"{original_name[0]}{counter}"
            counter += 1
            isChanged = True
        seen_names.add(designator)
        if isChanged:
            new_line = f"{designator} {' '.join(parts[1:])}"
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    return "\n".join(new_lines)


def modify_DC_bias(netlist, V_name, isVincrease):
    netlist = netlist.strip()
    lines = netlist.splitlines()
    new_V = float('inf')
    for line in lines:
        if V_name in line:
            part1, old_value = line.split("=")
            old_V = float(re.sub("\n", "", old_value).strip())
            if isVincrease:
                new_V = old_V * 1.1
            else:
                new_V = old_V * 0.9
            new_line = part1 + f"={new_V}"
            netlist = re.sub(line, new_line, netlist)
            break
    return netlist, new_V, old_V


def modify_ac_range_1T(netlist):
    lines = netlist.strip().split('\n')
    modified_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.lower().startswith('ac '):
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if 'wrdata' in next_line.lower():
                    match = re.search(r'ac\s+\w+\s+\d+\s+\d+\s+(\d+[GMK]?)', line, re.IGNORECASE)
                    if match:
                        old_freq = match.group(1)
                        if old_freq.upper() != '1T':
                            line = re.sub(r'\d+[GMK]?$', '1T', line, flags=re.IGNORECASE)
        modified_lines.append(line)
        i += 1
    return '\n'.join(modified_lines)


def modify_tran_step(netlist, min_step="50n"):
    lines = netlist.strip().split('\n')
    modified_lines = []
    for line in lines:
        original_line = line.strip()
        if original_line.lower().startswith('tran '):
            parts = original_line.split()
            if len(parts) >= 3:
                current_step = parts[1]
                current_value = _parse_time_value(current_step)
                min_value = _parse_time_value(min_step)
                if current_value < min_value:
                    parts[1] = min_step
                    new_line = ' '.join(parts)
                    modified_lines.append(new_line)
                    continue
        modified_lines.append(original_line)
    return '\n'.join(modified_lines)


def _parse_time_value(time_str):
    unit_multipliers = {
        'p': 1e-12,
        'n': 1e-9,
        'u': 1e-6,
        'm': 1e-3,
        'k': 1e3,
        'meg': 1e6,
        'g': 1e9,
        't': 1e12,
    }
    if time_str[-1].isdigit():
        return float(time_str)
    match = re.match(r'(\d+(?:\.\d+)?)([a-zA-Z]+)', time_str)
    if match:
        value = float(match.group(1))
        unit = match.group(2).lower()
        if unit in unit_multipliers:
            return value * unit_multipliers[unit]
        if unit == 's':
            return value
        print(f"Warning: Unknown time unit '{unit}' in '{time_str}', treating as seconds")
        return value
    try:
        return float(time_str)
    except ValueError:
        print(f"Warning: Could not parse time value '{time_str}', using 0")
        return 0.0


def ensure_data_format_settings(netlist):
    netlist = netlist.replace('\\n', '\n')
    lines = netlist.split('\n')
    has_units = False
    has_wr_vecnames = False
    control_index = -1
    for i, line in enumerate(lines):
        line_stripped = line.strip().lower()
        if line_stripped == '.control':
            control_index = i
        elif line_stripped == 'set units=degrees':
            has_units = True
        elif line_stripped == 'set wr_vecnames':
            has_wr_vecnames = True
    if control_index == -1:
        return netlist
    if has_units and has_wr_vecnames:
        return netlist
    insert_lines = []
    if not has_units:
        insert_lines.append('set units=degrees')
    if not has_wr_vecnames:
        insert_lines.append('set wr_vecnames')
    lines[control_index + 1:control_index + 1] = insert_lines
    return '\n'.join(lines)
