import sys
sys.path.append("./genai_agent")
import local_config


def make_technology_line(tech = "45nm"):
    return f"technology: {tech}" 
def make_cir_name_line(name = 9):
    return f'circuit_name: "{name}"'
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
        
        if prefix == 'm':
            # Multipliers are usually integers
            val_str = "[1, 25, 1]"
        elif prefix == 'w':
            val_str = f"[{w_min}, {w_max}, {w_step}]"
        elif prefix == 'l':
            val_str = f"[{l_min}, {l_max}, {l_step}]"
        else:
            # Fallback for things like 'cap' or 'res'
            val_str = "[!!float 0.1e-12, !!float 10.0e-12, !!float 0.1e-12]"
            
        lines.append(f"  {name}:  !!python/tuple {val_str}")# do not use \t or there will be error while reading
        
    return "\n".join(lines)
    
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
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []
    return sorted(list(params))

def get_targets(spec_ids):
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
    default_targets = local_config.default_targets
    
    # Convert to list if dict
    if isinstance(spec_ids, dict):
        spec_ids = list(spec_ids.keys())
    
    targets = {}
    
    for spec_id in spec_ids:
        if spec_id in local_config.table_target_id:
            metric_name = local_config.table_target_id[spec_id]
            metric_value = default_targets.get(spec_id, 0.0)
            targets[metric_name] = metric_value
    
    # Always include area (fixed)
    if 'area' not in targets:
        targets['area'] = 2.0e-9
    
    # Always include current (fixed)
    if 'current' not in targets:
        targets['current'] = 2.0e-4
    
    return targets

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
    for key in sorted(targets_dict.keys()):
        value = targets_dict[key]
        # Format value in scientific notation if very small
        if isinstance(value, float):
            lines.append(f"  {key}: !!float {value:.1e}")
        else:
            lines.append(f"  {key}: !!float {float(value):.1e}")
        keys.append(key)
    
    # Join keys with quotes and commas, no trailing comma
    str_keys = ", ".join(f"'{key}'" for key in keys)
    
    line_hard_constraints = f"hard_constraints: !!python/tuple [{str_keys}]"
    lines.append(line_hard_constraints)
    lines.append("optimization_targets: !!python/tuple ['area', 'current']")
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

def make_full_yaml(param_names, spec_ids=None, spec_weights=None, multiplier_value=2, tech='45nm'):
    """
    Build full YAML content and save to file from provided parameter list and target ids.

    Args:
        param_names (list): parameter names from .cir netlist (e.g., ['wp1','lp1','mp1',...])
        spec_ids (list): list of specification IDs (e.g., [0,3,4,6])
        spec_weights (dict): optional per-target weights (default 1.0 each)
        multiplier_value (int): multiplier value for m* elements in circuit_multipliers
        tech (str): technology string for top-level line

    Returns:
        str: combined YAML content
    """

    targets_dict = get_targets(spec_ids or [])
    targets_section = make_targets_lines(targets_dict)

    if spec_weights is None:
        spec_weights = {k: 1.0 for k in targets_dict.keys()}

    yaml_sections = [
        make_cir_name_line(),
        make_technology_line(tech),
        make_param_lines(param_names, tech),
        targets_section,
        make_spec_weights_lines(spec_weights),
        make_circuit_multipliers(param_names, multiplier_value),
    ]

    return "\n\n".join(yaml_sections)


def save_yaml(filename, param_names, spec_ids=None, spec_weights=None, multiplier_value=2, tech='45nm'):
    """Write full YAML content into filename."""
    content = make_full_yaml(param_names, spec_ids, spec_weights, multiplier_value, tech)
    with open(filename, 'w') as f:
        f.write(content)
    return filename