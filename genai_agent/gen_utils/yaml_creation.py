def get_circuit_name():
    return "9"
def get_technology():
    return "45nm" 
def get_params_old():
    # Parse the netlist to extract params
    netlist_path = r"d:\1kulStudy\8MA_Thesis\workplace\ngspice_interface\files\input_netlists\9\final_netlist.cir"
    with open(netlist_path, 'r') as f:
        lines = f.readlines()
    
    params = {}
    for line in lines:
        if line.strip().startswith('.param'):
            parts = line.strip().split()
            for part in parts[1:]:
                if '=' in part:
                    name, val = part.split('=')
                    # Convert units
                    if val.endswith('u'):
                        val_num = float(val[:-1]) * 1e-6
                    elif val.endswith('n'):
                        val_num = float(val[:-1]) * 1e-9
                    elif val.endswith('p'):
                        val_num = float(val[:-1]) * 1e-12
                    else:
                        try:
                            val_num = float(val)
                        except:
                            continue  # skip non-numeric
                    
                    # Map names: w0->wp1, l0->lp1, m0->mp1, w1->wn1, l1->ln1, m1->mn1
                    if name == 'w0':
                        new_name = 'wp1'
                    elif name == 'l0':
                        new_name = 'lp1'
                    elif name == 'm0':
                        new_name = 'mp1'
                    elif name == 'w1':
                        new_name = 'wn1'
                    elif name == 'l1':
                        new_name = 'ln1'
                    elif name == 'm1':
                        new_name = 'mn1'
                    else:
                        continue  # skip others like VB1, VDD
                    
                    # Create ranges
                    if new_name.startswith('w') or new_name.startswith('l'):
                        min_val = val_num / 2
                        max_val = val_num * 6
                        step = val_num / 2
                    elif new_name.startswith('m'):
                        min_val = 1
                        max_val = 25
                        step = 1
                    else:
                        min_val = val_num
                        max_val = val_num
                        step = 0
                    
                    params[new_name] = (min_val, max_val, step)
    
    # Create the YAML text
    text = "params:\n"
    for name in sorted(params.keys()):  # sort for consistency
        minv, maxv, step = params[name]
        text += f"  {name}:  !!python/tuple [{minv}, {maxv}, {step}]\n"
    return text
    
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

def hello():
    print ("h ello")
    
def write_yaml():
    return