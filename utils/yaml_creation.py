import sys

import yaml
sys.path.append(".")
from genai_agent.data import local_config
from utils import gen_utils
from utils import file_utils
from utils import user_interation_utils
def make_technology_line(tech = "45nm"):
    return f"technology: {tech}" 
def make_cir_name_line(name = 9):
    return f'circuit_name: "{name}"'  
  
def get_params(file_path):
    """
    Extract all parameter names from a .cir netlist file.
    
    Args:
        file_path (str): Path to the .cir file
        
    Returns:
        list: List of parameter names
    """
    params = set()  # use set to avoid duplicates
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            if line.strip().startswith('.param'):
                parts = line.strip().split()
                for part in parts[1:]:
                    if '=' in part:
                        name = part.split('=')[0]
                        params.add(name)
        
        params.discard("trf")# discard does not raise an error if the element is not there
        params.discard("period")
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []
    print(params)
    return sorted(list(params))

def make_param_lines(param_names, tech = "45nm"):
    
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
    
    for name in param_names:
        # Determine if it's a multiplier (m), width (w), or length (l)
        prefix = name[0].lower()
        print(f"Processing parameter: {name}, prefix: {prefix}")
        if prefix == 'm':
            # Multipliers are usually integers
            val_str = "[1, 25, 1]"
        elif prefix == 'w':
            val_str = f"[{w_min}, {w_max}, {w_step}]"
        elif prefix == 'l':
            val_str = f"[{l_min}, {l_max}, {l_step}]"
        elif prefix == 'v' or prefix == 'i':
            continue
        elif prefix == 'r':
            val_str = "[!!float 0, !!float 9.9e+3, !!float 100]"
            
        else:
            # Fallback for things like 'cap' 
            val_str = "[!!float 0.1e-12, !!float 10.0e-12, !!float 0.1e-12]"
            
        lines.append(f"  {name}:  !!python/tuple {val_str}")# do not use \t or there will be error while reading
        print(lines[-1])
    return "\n".join(lines)

def get_targets(spec_ids, spec_id_dict=None, spec_default_values=None):
    """
    Get target metrics based on specification IDs.
    
    Args:
        spec_ids (list or dict): List/dict of specification IDs
                                e.g., [0, 3, 4, 6] or {0: path, 3: path, ...}
                       
    Returns:
        dict: Dictionary mapping metric names to their target values
              e.g., {'gain': 20, 'noise': 3.0e-2, 'slew_rate': 15.0, ...}
    """
    
    # Default target values for each specification ID
    
    # Convert to list if dict
    if isinstance(spec_ids, dict):
        spec_ids = list(spec_ids.keys())
    
    targets = {}
    
    for spec_id in spec_ids:
        if spec_id in spec_id_dict:
            metric_name = spec_id_dict[spec_id]
            metric_default_value = spec_default_values.get(spec_id, 0.0) if spec_default_values else 0.0
            
            targets[metric_name] = metric_default_value
        else:
            raise ValueError(f"Specification ID {spec_id} is not recognized.")
    # Always include area (fixed)
    if 'area' not in targets:
        targets['area'] = 2.0e-6

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

def make_full_yaml(path, path_ids=None, cir_name = 9, spec_weights=None, multiplier_value=2, tech='45nm', data_for_dut_yaml=None, spec_id_dict=None, spec_default_values=None):
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
    params = get_params(path)
    
    targets_dict = get_targets(path_ids or [], spec_id_dict, spec_default_values)

    if spec_weights is None:
        spec_weights = {k: 1.0 for k in targets_dict.keys()}

    yaml_sections = [
        make_cir_name_line(cir_name),
        make_technology_line(tech),
        make_param_lines(params, tech),
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
    with open(path_temp, 'w') as f:
        yaml.dump(data, f)
#endregion save temp