import os
import re
import sys

import yaml
sys.path.append(".")
from genai_agent.data import local_config
from genai_agent.workflows import target_suggestion_agent
from utils import gen_utils
from utils import file_utils
from utils import user_interation_utils
def make_technology_line(tech = "45nm"):
    return f"technology: {tech}" 
def make_cir_name_line(name = 9):
    return f'circuit_name: "{name}"'  
  
def get_param_definitions(file_path):
    """Return .param names mapped to their original netlist values."""
    definitions = {}
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if not line.strip().lower().startswith('.param'):
                    continue
                uncommented = line.split(';', 1)[0].split('$', 1)[0]
                for name, value in re.findall(r"([A-Za-z_]\w*)\s*=\s*([^\s]+)", uncommented):
                    definitions[name] = value
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return {}
    return definitions


def _parse_spice_number(value):
    """Parse a simple SPICE number into SI units; return None for expressions."""
    if value is None:
        return None
    match = re.fullmatch(
        r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)([A-Za-z]+)?",
        str(value).strip(),
        re.IGNORECASE,
    )
    if not match:
        return None
    suffix = (match.group(2) or "").lower()
    multipliers = {
        "": 1.0,
        "t": 1e12,
        "g": 1e9,
        "meg": 1e6,
        "k": 1e3,
        "m": 1e-3,
        "u": 1e-6,
        "n": 1e-9,
        "p": 1e-12,
        "f": 1e-15,
    }
    multiplier = multipliers.get(suffix)
    if multiplier is None:
        return None
    return float(match.group(1)) * multiplier


def _bias_parameter_kind(name):
    """Classify explicit external bias parameters without capturing signal inputs."""
    canonical = re.sub(r"_?val$", "", name.lower())
    if canonical in {"vin_bias", "vcm_bias"}:
        return "voltage"
    if canonical == "iin_bias":
        return "current"
    if re.fullmatch(r"(?:vbias|vb)\d*", canonical):
        return "voltage"
    if re.fullmatch(r"(?:ibias|ib)\d*", canonical):
        return "current"
    return None


def make_param_lines(param_names, tech="45nm", param_values=None, supply_voltage=1.2):
    # Define tech-specific constants
    if tech == "45nm":
        l_min = "45.0e-09"
        l_max = "225.0e-09"
        l_step = "45.0e-09"
        w_min = "2.50e-07"
        w_max = "30.0e-07"
        w_step = "2.50e-07"
    else:
        # Default or other tech nodes (e.g., 180nm)
        l_min, l_max, l_step = "180.0e-09", "900.0e-09", "180.0e-09"
        w_min, w_max, w_step = "5.0e-07", "50.0e-07", "5.0e-07"

    lines = ["params:"]
    param_values = param_values or {}
    fixed_parameters = {
        "vdd",
        "vdd_val",
        "vss",
        "gnd",
        "trf",
        "period",
        "temp_pvt",
        "vhigh",
        "vlow",
        "vcm",
        "icmv",
        "vref",
    }

    for name in param_names:
        prefix = name[0].lower()
        normalized_name = name.lower()
        bias_kind = _bias_parameter_kind(name)
        print(f"Processing parameter: {name}, prefix: {prefix}")

        if normalized_name in fixed_parameters or normalized_name.startswith(("vclk", "clk")):
            continue
        if bias_kind == "voltage":
            voltage_step = supply_voltage / 24.0
            val_str = (
                f"[!!float 0.0, !!float {supply_voltage:.6g}, "
                f"!!float {voltage_step:.6g}]"
            )
        elif bias_kind == "current":
            nominal = _parse_spice_number(param_values.get(name))
            if nominal is None or nominal <= 0:
                current_min, current_max = 1e-6, 1e-3
            else:
                current_min = max(nominal / 10.0, 1e-12)
                current_max = nominal * 10.0
            current_step = (current_max - current_min) / 100.0
            val_str = (
                f"[!!float {current_min:.6g}, !!float {current_max:.6g}, "
                f"!!float {current_step:.6g}]"
            )
        elif prefix == 'm':
            val_str = "[1, 25, 1]"
        elif prefix == 'w':
            val_str = f"[{w_min}, {w_max}, {w_step}]"
        elif prefix == 'l':
            val_str = f"[{l_min}, {l_max}, {l_step}]"
        elif prefix == 'v' or prefix == 'i':
            # Signal inputs and testbench controls are not sizing parameters.
            continue
        elif prefix == 'r':
            val_str = "[!!float 0, !!float 9.9e+3, !!float 100]"
        else:
            # Fallback for things like 'cap'
            val_str = "[!!float 0.1e-12, !!float 10.0e-12, !!float 0.1e-12]"

        lines.append(f"  {name}:  !!python/tuple {val_str}")
        print(lines[-1])
    return "\n".join(lines)

def _normalize_spec_id(spec_id):
    if isinstance(spec_id, str) and spec_id.isdigit():
        return int(spec_id)
    return spec_id


def _get_default_value(spec_id, spec_default_values):
    if not spec_default_values:
        return 0.0
    if spec_id in spec_default_values:
        return spec_default_values[spec_id]
    if isinstance(spec_id, int) and str(spec_id) in spec_default_values:
        return spec_default_values[str(spec_id)]
    if isinstance(spec_id, str) and spec_id.isdigit():
        int_id = int(spec_id)
        if int_id in spec_default_values:
            return spec_default_values[int_id]
    return 0.0


def get_targets(spec_ids, spec_id_dict=None, spec_default_values=None, target_context=None, is_target_suggest=False):
    """
    Get target metrics based on specification IDs.
    
    Args:
        spec_ids (list or dict): List/dict of specification IDs
                                e.g., [0, 3, 4, 6] or {0: path, 3: path, ...}
                       
    Returns:
        dict: Dictionary mapping metric names to their target values
              e.g., {'gain': 20, 'noise': 3.0e-2, 'slew_rate': 15.0, ...}
    """
    
    # Convert to list if dict
    if isinstance(spec_ids, dict):
        spec_ids = list(spec_ids.keys())
    
    targets = {}
    
    for spec_id in spec_ids:
        normalized_id = _normalize_spec_id(spec_id)
        match_id = None
        if spec_id_dict is not None:
            if normalized_id in spec_id_dict:
                match_id = normalized_id
            elif isinstance(normalized_id, int) and str(normalized_id) in spec_id_dict:
                match_id = str(normalized_id)
            elif isinstance(normalized_id, str) and normalized_id.isdigit() and int(normalized_id) in spec_id_dict:
                match_id = int(normalized_id)

        if match_id is None:
            raise ValueError(f"Specification ID {spec_id} is not recognized.")

        metric_name = spec_id_dict[match_id]
        metric_default_value = _get_default_value(match_id, spec_default_values)
        targets[metric_name] = metric_default_value

    # Always include area (fixed)
    if 'area' not in targets:
        targets['area'] = 2.0e-6

    suggestion = target_suggestion_agent.suggest_target_values(targets, target_context)
    target_suggestion_agent.print_suggestions(suggestion)
    if is_target_suggest:
        targets = suggestion["targets"]

    targets = user_interation_utils.user_input_targets(targets)
    
    # Not Always include current 
    # if 'current' not in targets:
    #     targets['current'] = 2.0e-1
    
    return targets


def _format_value(value):# start with underline, this will not be imported
    """Format a value for YAML: use scientific notation for very small/large, normal for rest."""
    fval = float(value)
    # Use scientific notation if very small (< 1e-5) or very large (> 1e6)
    if abs(fval) < 1 or abs(fval) > 1e3:
        return f"{fval:.1e}"
    else:
        # For normal range, use appropriate precision
        return f"{fval:.2f}" 
 

def make_targets_lines(targets_dict):
    """
    Create YAML text for the targets section.
    
    Args:
        targets_dict (dict): Dictionary of target metrics
                           e.g., {'area': 2.0e-9, 'gain': 200, ...}
                           
    Returns:
        str: YAML formatted targets section
    """
    lines = ["targets:"]
    keys = []
    has_current = False
    for key in sorted(targets_dict.keys()):
        value = targets_dict[key]
        formatted_value = _format_value(value)
        lines.append(f"  {key}: !!float {formatted_value}")
        if key == 'current':
            has_current = True
        keys.append(key)
    
    # Join keys with quotes and commas, no trailing comma
    str_keys_hard = ", ".join(f"'{key}'" for key in keys if key != 'area' and key != 'current')
    
    line_hard_constraints = f"hard_constraints: !!python/tuple [{str_keys_hard}]"
    lines.append(line_hard_constraints)
    if has_current:
        lines.append("optimization_targets: !!python/tuple ['area', 'current']")
    else:
        lines.append("optimization_targets: !!python/tuple ['area']")

    return "\n".join(lines)

def make_spec_weights_lines(spec_weights_dict):
    lines = ["spec_weights:"]
    for key in sorted(spec_weights_dict.keys()):
        value = 1.0
        # Format value in scientific notation if very small
        if isinstance(value, float):
            lines.append(f"  {key}: !!float {value:.1f}")
        else:
            lines.append(f"  {key}: !!float {float(value):.1f}")
    return "\n".join(lines)

def make_circuit_multipliers(param_names, multiplier_value=2):
    """
    Create YAML text for circuit_multipliers section from parameter names.

    Args:
        param_names (list): List of parameter names that include 'l', 'w', 'm', 'C'.
        multiplier_value (int): Value to assign to each multiplier.

    Returns:
        str: YAML formatted circuit_multipliers section.
    """
    # Pick only multiplier parameters that are named with m and not mixed
    multipliers = [name for name in param_names if name.lower().startswith('m')]
    
    if not multipliers:
        return "circuit_multipliers:\n"

    lines = ["circuit_multipliers:"]
    for name in sorted(multipliers):
        lines.append(f"  {name}: !!int {multiplier_value}")
    return "\n".join(lines)

def make_path_id_to_yaml(path_id_dict, root_name='path_id'):
    """
    Convert a path ID dictionary into YAML text.

    Args:
        path_id_dict (dict): Dictionary of IDs to path strings.
                             e.g. {18: './genai_agent/output/96/ac_dm.csv'}
        root_name (str): Top-level YAML key name.

    Returns:
        str: YAML formatted path_id section.
    """
    data = {root_name: path_id_dict}
    
    # yaml.dump automatically handles lists, strings, and integers perfectly
    # default_flow_style=None keeps lists clean on one line if short, or multi-line if long
    return yaml.dump(data, default_flow_style=None, sort_keys=True)

def make_dut_yaml_lines(data_for_dut_yaml):
    """
    Create YAML text for DUT-specific configuration data.

    Args:
        data_for_dut_yaml (tuple): Tuple containing (is_differential, has_input, target_dc_vout)
                                   e.g., (False, True, 1.2)

    Returns:
        str: YAML formatted dut_config section, or empty string if data_for_dut_yaml is None
    """
    if data_for_dut_yaml is None:
        return ["dut_config: None"]
    
    if len(data_for_dut_yaml) < 3:
        return ["dut_config: None"]
    
    is_differential = data_for_dut_yaml[0]
    has_input = data_for_dut_yaml[1]
    target_dc_vout = data_for_dut_yaml[2]
    
    lines = ["dut_config:"]
    lines.append(f"  is_differential: !!bool {str(is_differential).lower()}")
    lines.append(f"  has_input: !!bool {str(has_input).lower()}")
    lines.append(f"  target_dc_vout: !!float {float(target_dc_vout)}")
    
    return "\n".join(lines)

def make_full_yaml(path, path_ids=None, cir_name = 9, spec_weights=None, multiplier_value=2, tech='45nm', data_for_dut_yaml=None, spec_id_dict=None, spec_default_values=None, target_context=None):
    """
    Build full YAML content and save to file from provided parameter list and target ids.

    Args:
        params (list): parameter names from .cir netlist (e.g., ['wp1','lp1','mp1',...])
        spec_ids (list): list of specification IDs (e.g., [0,3,4,6])
        spec_weights (dict): optional per-target weights (default 1.0 each)
        multiplier_value (int): multiplier value for m* elements in circuit_multipliers
        tech (str): technology string for top-level line

    Returns:
        str: combined YAML content
    """
    param_values = get_param_definitions(path)
    params = sorted(param_values)
    params = [name for name in params if name not in {"trf", "period"}]
    
    target_context = dict(target_context or {})
    target_context.setdefault("netlist_path", path)
    target_context.setdefault("cir_name", cir_name)
    target_context.setdefault("data_for_dut_yaml", data_for_dut_yaml)
    target_context.setdefault("tech", tech)

    targets_dict = get_targets(path_ids or [], spec_id_dict, spec_default_values, target_context=target_context)

    if spec_weights is None:
        spec_weights = {k: 1.0 for k in targets_dict.keys()}

    yaml_sections = [
        make_cir_name_line(cir_name),
        make_technology_line(tech),
        make_param_lines(params, tech, param_values=param_values),
        make_targets_lines(targets_dict),
        make_spec_weights_lines(spec_weights),
        make_circuit_multipliers(params, multiplier_value),
        make_path_id_to_yaml(path_ids),
        make_dut_yaml_lines(data_for_dut_yaml)
    ]


    content = "\n\n".join(yaml_sections)
    path_yaml = local_config.path_yaml+f"{cir_name}.yaml"
    file_utils.save_str_to_file(content, path_yaml)
    return path_yaml

def update_yaml_targets(yaml_path, targets_dict):
    """
    Update the targets section in an existing YAML file with new values.
    
    Args:
        yaml_path (str): Path to the YAML file to update
        targets_dict (dict): Dictionary of target metrics and their new values
                            e.g., {'area': 2.0e-6, 'gain': 200, 'dc_output_voltage': 1.2}
    
    Returns:
        None (file is updated in place)
    """
    try:
        # Load existing YAML
        with open(yaml_path, 'r') as f:
            yaml_data = yaml.safe_load(f)
        
        # Update targets section
        if 'targets' not in yaml_data:
            yaml_data['targets'] = {}
        
        for key, value in targets_dict.items():
            yaml_data['targets'][key] = float(value)
        
        # Preserve the structure by reconstructing the file manually
        # to maintain the original formatting and comments
        with open(yaml_path, 'r') as f:
            lines = f.readlines()
        
        # Find the targets section and update values
        updated_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if we're entering the targets section
            if line.strip().startswith('targets:'):
                updated_lines.append(line)
                i += 1
                
                # Process all target entries until we hit a new section (non-indented line)
                while i < len(lines):
                    current_line = lines[i]
                    
                    # Check if we've left the targets section (next section starts)
                    if current_line.strip() and not current_line.startswith('  ') and current_line.strip() != 'targets:':
                        break
                    
                    # If it's a target entry (starts with 2 spaces and contains ':')
                    if current_line.startswith('  ') and ':' in current_line and not current_line.strip().startswith('#'):
                        # Parse the target name
                        parts = current_line.split(':')
                        target_name = parts[0].strip()
                        
                        # If this target is in our update dict, replace the value
                        if target_name in targets_dict:
                            new_value = _format_value(targets_dict[target_name])
                            updated_lines.append(f"  {target_name}: !!float {new_value}\n")
                        else:
                            updated_lines.append(current_line)
                    else:
                        updated_lines.append(current_line)
                    
                    i += 1
            else:
                updated_lines.append(line)
                i += 1
        
        # Write back to file
        with open(yaml_path, 'w') as f:
            f.writelines(updated_lines)
        
        print(f"Successfully updated targets in {yaml_path}")
        
    except Exception as e:
        print(f"Error updating YAML targets in {yaml_path}: {e}")
#region save temp
def save_temp(data):
    i = data['cir_name']
    path_temp = f'.\\genai_agent\\output\\{i}\\temp.yaml'
    os.makedirs(os.path.dirname(path_temp), exist_ok=True)
    with open(path_temp, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)
#endregion save temp
