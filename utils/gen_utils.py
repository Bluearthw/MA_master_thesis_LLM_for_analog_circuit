import re
import time
import os
# import pandas as pd

# import scipy.interpolate as interp
# import scipy.optimize as sciopt

# import matplotlib.pyplot as plt
import json
# from scipy.integrate import trapezoid
import sys
import difflib
##### local
from genai_agent.data import local_config
from utils import file_utils
DEFAULT_W = "0.5u"
DEFAULT_L = "90n"
DEFAULT_M = "1"
DEFAULT_R = "1k"
DEFAULT_C = "3p"




# region for classification
def find_all(dataset_path):
    i = 4
    exist_nums = []
    lines_to_read = 7 # in the file, it is 1 line per empty line
    while True:
        path_nl = dataset_path + f"/{i}/{i}.cir"
        if os.path.isfile(path_nl):
            exist_nums.append(i)
        i+=1
        if i > 1044:
            break
            
        # print("i\n",i)

    return exist_nums

       
def find_OPAMP_num_from_file(dataset_path):
    # 4 to 1044
    i = 4
    exist_nums = []
    lines_to_read = 7 # in the file, it is 1 line per empty line
    while True:

        path_nl = dataset_path + f"/{i}/{i}.cir"
        if os.path.isfile(path_nl):
        # print("path_nl",path_nl)
        # let's check cir file first, only when it has vin
            ports_name_to_check = ["VIN1","VOUT1"]
            if are_ports_all_exist(path_nl,ports_name_to_check):
                # if VIN1 exists, continue
                path = dataset_path + f"/{i}/edited_explanation.md"
                # print("path",path)
                lines = file_utils.get_file_to_lines(path, lines_to_read)
                for line in lines:
                    if "amplifier" in line or "Amplifier" in line :
                        exist_nums.append(i)
                        break
        # counter part
        i+=1
        if i > 1044:
            break
            
        # print("i\n",i)

    return exist_nums

def find_OPAMPs_without_clk(dataset_path, nums):
    exist_nums = []
    # no differential, no current output, not clock
    for i in nums:
        path_nl = dataset_path + f"/{i}/{i}.cir"
        if os.path.isfile(path_nl):
        # print("path_nl",path_nl)
        # let's check cir file first, only when it has vin
            ports_name_to_check = local_config.mixer_comparator_ports 
            # print(ports_name_to_check)
            if not is_port_exist(path_nl,ports_name_to_check):
                exist_nums.append(i)

    return exist_nums
def find_SISOs_from_OPAMPs(dataset_path, nums):
    exist_nums = []
    # no differential, no current output, not clock
    for i in nums:

        path_nl = dataset_path + f"/{i}/{i}.cir"
        if os.path.isfile(path_nl):
            # print("path_nl",path_nl)
        # let's check cir file first, only when it has vin
            ports_name_to_check = local_config.differential_ports
            # print(ports_name_to_check)
            if not is_port_exist(path_nl,ports_name_to_check):
                exist_nums.append(i)

    return exist_nums

def difference_of_nums(nums_big, nums2):
    #the first list is the bigger one.
    difference = list(set(nums_big).difference(set(nums2)))
    print("# ", len(difference))
    print(sorted(difference))

def find_cir_num_without_pattern(dataset_path,name_to_check,nums = local_config.num_all):
    exist_nums = []
    for i in nums:

        path_nl = dataset_path + f"/{i}/{i}.cir"
        if os.path.isfile(path_nl):
            # let's check cir file first, only when it has vin
        
            if not is_port_exist(path_nl,name_to_check):
                exist_nums.append(i)
            # counter part
    return exist_nums

def find_cir_num_with_pattern(dataset_path,name_to_check,nums = local_config.num_all):
    exist_nums = []
    for i in nums:


        path_nl = dataset_path + f"/{i}/{i}.cir"
        if os.path.isfile(path_nl):
            # let's check cir file first, only when it has vin
        
            if is_port_exist(path_nl,name_to_check):
                exist_nums.append(i)
            # counter part
    
    return exist_nums

def find_RF_from_cir_str(path_exaplain, cir_string):
    # start_time = time.perf_counter()
    if "L0" in cir_string:
        return True
    lines = file_utils.get_file_to_lines(path_exaplain,10,True)
    
    for line in lines:
        if "RF" in line:
            return True
    lines2 = file_utils.get_file_to_lines(path_exaplain,8)
    string = "".join(lines2)
    if "RF" in string:
        # end_time = time.perf_counter()
        # print("time used",end_time-start_time)
        return True

    return False

def find_ports_from_cir_nums(dataset_path,nums = list(range(4,1045))):
    '''
    Default is all cir nums
    '''
    exist_ports = []
    for i in nums:
        path = dataset_path + f"/{i}/Port{i}.txt"
        # print(path)
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding='utf-8') as file:
                    # print("File exists and is ready to read.")
                    # read 10 lines from the file
                    cir_string = file.read() # https://www.askpython.com/python/examples/read-multiple-lines-python
                    # print(cir_string)
                    cir_string = re.sub('\n',"",cir_string)
                    # print(cir_string)
                    ports = cir_string.split(" ")
                    
                    for port in ports:
                        if port in exist_ports:
                            
                            continue
                        else:
                            exist_ports.append(port)
            except FileNotFoundError:
                print("???")
        # if(i > 220):
        #     break
    # exist_ports.remove('')
    return exist_ports

def find_num_from_class(class_id):
    exist_nums = []
    for i in local_config.num_all:

        path = local_config.path_classified_dataset + f"/{i}/detected_class.txt"
        if int(file_utils.get_file_to_str(path)) == class_id:
            exist_nums.append(i)
            # counter part
        
    return exist_nums

def find_cat_from_num(num):
    path = local_config.path_classified_dataset+ f"/{num}/detected_class.txt"
    return int(file_utils.get_file_to_str(path))
# endregion for classification



# region for adding (tool)

def match_transistor(match):

    if match:
        # Found an M-line
        transistor_id = match.group(1)  # e.g., M1
        nodes_and_model = match.group(2)  # e.g., VOUT2 VIN2 IB1 VSS nmos

        # Extract the numerical part of the ID for parameter naming (e.g., 1 from M1)
        # This makes the parameters w1, l1, m1
        try:
            # Use re.findall to safely extract all digits from the ID
            num_id = "".join(re.findall(r"\d+", transistor_id))
        except:
            # Fallback if no number is found (e.g., if ID is M_core)
            num_id = transistor_id.replace("M", "_")

        # --- Detect transistor type (NMOS or PMOS) ---
        if "nmos" in nodes_and_model.lower():
            prefix = "n"  # e.g., wn1, ln1, mn1
        elif "pmos" in nodes_and_model.lower():
            prefix = "p"  # e.g., wp1, lp1, mp1
        else:
            prefix = ""   # Fallback to original w1, l1, m1

        # --- Generate Parameter Names ---
        w_param = f"w{prefix}{num_id}"
        l_param = f"l{prefix}{num_id}"
        m_param = f"m{prefix}{num_id}"

        # --- Create .param statement ---
        param_line = (
            f".param {w_param}={DEFAULT_W} {l_param}={DEFAULT_L} {m_param}={DEFAULT_M}"
        )

        # Only add if we haven't processed this transistor number yet
        # (Important for files with comments or multiple blocks)
        # if num_id not in transistor_ids:
        #     param_statements.append(param_line)
        #     transistor_ids.append(num_id)

        # --- Create modified M-line ---
        new_transistor_id = f"m{prefix}{num_id}"
        new_m_line = (
            f"{new_transistor_id} {nodes_and_model} w={w_param} l={l_param} m={m_param}"
        )
        return new_m_line, num_id, param_line

        # Keep other lines as is (resistors, capacitors, sources, etc.)


def match_RC(match, digit_extractor):
    if match:
        component_id = match.group(1)  # R0, C1, etc.
        node1 = match.group(2)
        node2 = match.group(3)
        # Note: We ignore the original value (match.group(4)) since we replace it

        num_id_list = digit_extractor.findall(component_id)
        param_identifier = (
            "".join(num_id_list)
            if num_id_list
            else component_id.replace(component_id[0], "_")
        )

        component_type = component_id[0].lower()  # 'r' or 'c'

        param_name = f"{component_type}{param_identifier}"
        default_value = DEFAULT_R if component_type == "r" else DEFAULT_C

        param_line = f".param {param_name}={default_value}"

        # Check for uniqueness and add .param line

        # --- Create modified R/C line ---
        # Format: R<id> <node1> <node2> {<param_name>}
        new_rc_line = f"{component_id} {node1} {node2} {{{param_name}}}"
        return new_rc_line, param_line, param_identifier, component_type


def add_params(netlist):  # input should be lines here
    """
    Add parameters to the transistors, resistors and capacitors in the incomplete spice netlist.

    Performs the following transformations on the input netlist string:
    1. Add .param lines.
    2. Add w, l, m to the transistors
    3. Add {value} to resistor and capacitors
    Args:
        netlist: The raw, potentially incomplete or flawed SPICE netlist content as a single string.

    Returns:
        The netlist added with parameters as a string.
    """
    param_statements = []
    modified_lines = []
    transistor_ids = []
    resistor_ids_processed = set()
    capacitor_ids_processed = set()
    m_line_pattern = re.compile(r"^(M\S+)\s+(.+?)$", re.IGNORECASE) # ^ start of line
    #[RC], either 'R' or 'C'    \Rs+, match 1 more which is not white space
    rc_line_pattern = re.compile(r"^([RC]\S+)\s+(\S+)\s+(\S+)$", re.IGNORECASE)
    digit_extractor = re.compile(r"\d+")
    lines = netlist.strip().split("\n")
    for line in lines:
        line = line.strip()
        # print("line", line)
        # skip empty lines and comments
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
    # add tran param
    param_tran_line = [".param trf=0.5u ; for slew-rate calculation",".param period=10u "]
    output = []
    output.append("*params ")
    output.extend(param_statements)
    output.extend(param_tran_line)
    output.extend(modified_lines)

    return "\n".join(output)


def add_DC_source(netlist, vdd="1.2", vb1="0.7", ib1 = "0.01"):
    """
    Add DC source to the incomplete spice netlist if it is needed.

    Performs the following transformations on the input netlist string:
    1. Check if VDD and VSS is used.
    2. Add source if needed.
    Args:
        netlist: The raw, potentially incomplete or flawed SPICE netlist content as a single string.

    Returns:
        The netlist added with parameters as a string.
    """
    param_line = f"\n.param VDD_VAL={vdd}"
    param_line_vb1 = f"\n.param VB1_VAL={vb1}"
    param_line_ib1 = f"\n.param IB1_VAL={ib1}"

    # Standard source definitions using the parameter
    vdd_source = "\nvdd VDD 0 dc=VDD_VAL"
    vss_source = "\nvss VSS 0 dc=0"  # VSS is typically ground reference
    vb1_source = "\nvb1 VB1 0 dc=VB1_VAL"  # VSS is typically ground reference
    ib1_source = "\nib1 IB1 0 dc=IB1_VAL"  # VSS is typically ground reference

    # source_block = f"\n{param_line}\n{vdd_source}\n"
    # vss_block = f"{vss_source}\n"
    # --- 2. Check for Node Usage ---

    # This regex looks for VDD or VSS surrounded by word boundaries (\b),
    # ensuring it's not part of a longer word (like 'VSS_test').
    # We use re.DOTALL to search across multiple lines.
    vdd_in_use = re.search(r"\bVDD\b", netlist, re.IGNORECASE)
    vss_in_use = re.search(r"\bVSS\b", netlist, re.IGNORECASE)
    vb_in_use = re.search(r"\bVB1\b", netlist, re.IGNORECASE)
    ib_in_use = re.search(r"\bIB1\b", netlist, re.IGNORECASE)

    # --- 3. Determine Insertion Point and Insert ---

    insertion_point = 0
    for i, line in enumerate(netlist.splitlines()):
            line_stripped = line.strip()

            if line_stripped and (
                line_stripped[0].isalpha() or line_stripped.startswith(".")
            ):
                insertion_point = i
                break
    if vdd_in_use:

        lines = netlist.splitlines()
        # Insert the source block at the determined point
        # We replace the line at insertion_point with itself + the new block
        lines.insert(insertion_point, param_line)

        lines.insert(len(lines), vdd_source)

    if ib_in_use:
        lines = netlist.splitlines()
        lines.insert(insertion_point, param_line_ib1)
        lines.insert(len(lines), ib1_source)

    if vb_in_use:
        lines.insert(insertion_point, param_line_vb1)
        lines.insert(len(lines), vb1_source)

    if vss_in_use:

        lines.insert(len(lines), vss_source)
    else:
        print("VSS nodes not found in netlist. Skipping DC source addition.")
        return netlist
    return "\n".join(lines)


def add_C_load(netlist, node="VOUT1", Cload="10p"):
    """
    Add load capacitance to the incomplete spice netlist.

    Performs the following transformations on the input netlist string:
    1. Add load capacitance.
    Args:
        netlist: The raw, potentially incomplete or flawed SPICE netlist content as a single string.
        node: The node that Cload should connected to
    Returns:
        The netlist added with parameters as a string.
    """
    # isUsed = re.search(r'\bVDD\b', circuit_string, re.IGNORECASE)
    param_line = f"\n.param Cload={Cload}"
    cload_line = f"\nCload {node} VSS " + "{Cload}"

    lines = netlist.strip().splitlines()

    # Insert the source block at the determined point
    # We replace the line at insertion_point with itself + the new block
    lines.insert(2, param_line)
    lines.insert(len(lines), cload_line)

    return "\n".join(lines)


def add_OP_simulation(netlist, node="vin1", VINCM="0.6"):
    """
    Add DC input to the incomplete spice netlist.

    Performs the following transformations on the input netlist string:
    1. Add DC input.
    Args:
        netlist: The raw, potentially incomplete or flawed SPICE netlist content as a single string.
        node: The node that Cload should connected to
    Returns:
        The netlist added with OP simulation as a string.
    """
    # isUsed = re.search(r'\bVDD\b', circuit_string, re.IGNORECASE)
    param_line = f"\n.param VINCM={VINCM}"
    vincm_line = f"\nVicm {node} VSS dc=VINCM"
    # temp_line = "\n.param temperature=25.0"
    op_sim_block = """
.control

option numdgt=4
set temp=25
op
.endc
.end
"""
    lines = netlist.strip().splitlines()

    # Insert the source block at the determined point
    # We replace the line at insertion_point with itself + the new block
    lines.insert(2, param_line)
    # lines.insert(2, temp_line)
    lines.insert(len(lines), vincm_line)
    lines.insert(len(lines), op_sim_block)

    return "\n".join(lines)

def add_AC_simulation(netlist, node="VIN1"):
    
    # isUsed = re.search(r'\bVDD\b', circuit_string, re.IGNORECASE)
    VinDM_line = f"\nVinDM {node} VSS dc=0 ac = 1"
    # temp_line = "\n.param temperature=25.0"
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
    lines.insert(0,"* title line\n")
    return "\n".join(lines)

def add_control(netlist):
    # isUsed = re.search(r'\bVDD\b', circuit_string, re.IGNORECASE)
    # temp_line = "\n.param temperature=25.0"
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
    lines.insert(0,"* title line\n")
    return "\n".join(lines)
        

# endregion for adding


# region for modifying
def clean_netlist(netlist):
    """
    Cleans an analog SPICE netlist string by standardizing component names and removing
    descriptive text.

    Performs the following transformations on the input netlist string:
    1. Removes all parentheses '(', ')'.
    2. Renames the device model 'nmos4' to 'nmos' and 'pmos4' to 'pmos'.
    3. Removes the descriptive words 'resistor' and 'capacitor' and replaces them
       with a newline character, effectively removing them from the component definition line.
    4. Add inclusion
    Args:
        netlist: The raw, potentially incomplete or flawed SPICE netlist content as a single string.

    Returns:
        The cleaned and standardized SPICE netlist string.
    """
    netlist = netlist.strip()

    netlist = re.sub(r"[()]", "", netlist)

    netlist = re.sub(r"\bnmos4\b", "nmos", netlist)
    netlist = re.sub(r"\bpmos4\b", "pmos", netlist)
    netlist = re.sub(r"\s*resistor\s*", "\n", netlist, flags=re.IGNORECASE)
    netlist = re.sub(r"\s*capacitor\s*", "\n", netlist, flags=re.IGNORECASE)

    return local_config.str_nl_include + netlist

def clean_before_CMFB(netlist):
    """
    Remove the simulation block from the netlist.
    Specifically, removes lines from the last 'set' command to '.endc' inclusive.
    This cleans the netlist before adding CMFB simulation.
    """
    lines = netlist.strip().splitlines()
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('set'):
            start_idx = i  # update to the last 'set' line
        elif stripped == '.endc':
            end_idx = i
            break
    if start_idx is not None and end_idx is not None and start_idx < end_idx:
        # Remove from start_idx to end_idx inclusive
        new_lines = lines[:start_idx + 1] + lines[end_idx :] # do not + 1 since .endc is still needed
        return '\n'.join(new_lines)
    else:
        # If no such block found, return the netlist unchanged
        return netlist

def modify_duplicate_component(circuit_string):
    seen_names = set()
    new_lines = []
    
    for line in circuit_string.strip().splitlines():
        parts = line.split()
        if not parts: # Skip empty lines
            new_lines.append(line)
            continue
            
        designator = parts[0]
        original_name = designator
        counter = 0
        isChanged = False
        # If the name exists, keep adding to the counter until we find a unique name
        # e.g., C1 -> C0 -> C1 -> C2
        while designator in seen_names:
            designator = f"{original_name[0]}{counter}"
            counter += 1
            isChanged = True
        seen_names.add(designator)
        if isChanged:
        # Rebuild the line with the (potentially new) designator
            new_line = f"{designator} {' '.join(parts[1:])}"
            new_lines.append(new_line)
        else:
            new_lines.append(line)
        
    return "\n".join(new_lines)


def modify_DC_bias(netlist, V_name, isVincrease):
    netlist = netlist.strip()
    lines = netlist.splitlines()
    new_V = float("inf")
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
    """
    Modify AC sweep range to extend upper frequency to 1T (1 THz).
    
    Looks for lines starting with 'ac' (case-insensitive) followed by 'ac_gain' in wrdata line.
    Replaces any upper frequency value (e.g., 100G, 10G, 1G) with 1T.
    
    Args:
        netlist (str): The SPICE netlist content as a string.
        
    Returns:
        str: Modified netlist with extended AC ranges to 1T.
    """
    lines = netlist.strip().split('\n')
    modified_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if current line starts with 'ac' (case-insensitive)
        if line.lower().startswith('ac '):
            
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if 'wrdata' in next_line.lower():# i think ac_gain is not needed but wrdata is needed
                    # Replace upper frequency with 1T using regex
                    # Pattern: ac dec 10 1 <frequency>
                    # Match any frequency value (e.g., 100G, 10G, 1G, 1000M, etc.)
                    match = re.search(r'ac\s+\w+\s+\d+\s+\d+\s+(\d+[GMK]?)', line, re.IGNORECASE)
                    if match:
                        old_freq = match.group(1)
                        if old_freq.upper() != '1T':
                            line = re.sub(r'\d+[GMK]?$', '1T', line, flags=re.IGNORECASE)
                            print(f"[modify_ac_range_1T] Extended AC range from {old_freq} to 1T: {line}")
        
        modified_lines.append(line)
        i += 1
    
    return '\n'.join(modified_lines)

def modify_tran_step(netlist, min_step="50n"):
    """
    Modify transient simulation step time to be at least the specified minimum.
    
    Looks for lines starting with 'tran' (case-insensitive) and ensures the step time
    is at least the minimum value (default 50n).
    
    Args:
        netlist (str): The SPICE netlist content as a string.
        min_step (str): Minimum step time (default "50n").
        
    Returns:
        str: Modified netlist with adjusted transient step times.
    """
    lines = netlist.strip().split('\n')
    modified_lines = []
    
    for line in lines:
        original_line = line.strip()
        
        # Check if current line starts with 'tran' (case-insensitive)
        if original_line.lower().startswith('tran '):
            # Parse the line: tran <step> <stop>
            parts = original_line.split()
            if len(parts) >= 3:  # tran <step> <stop> [other options]
                current_step = parts[1]
                
                # Convert step times to comparable values
                current_value = _parse_time_value(current_step)
                min_value = _parse_time_value(min_step)
                
                if current_value < min_value:
                    # Replace the step time
                    parts[1] = min_step
                    new_line = ' '.join(parts)
                    print(f"[modify_tran_step] Increased step time from {current_step} to {min_step}: {new_line}")
                    modified_lines.append(new_line)
                else:
                    modified_lines.append(original_line)
            else:
                modified_lines.append(original_line)
        else:
            modified_lines.append(original_line)
    
    return '\n'.join(modified_lines)

def _parse_time_value(time_str):
    """
    Parse SPICE time string (e.g., '10n', '1u', '100p') to numeric value in seconds.
    
    Args:
        time_str (str): Time string with unit suffix
        
    Returns:
        float: Time value in seconds
    """
    # Unit multipliers (case insensitive)
    unit_multipliers = {
        'p': 1e-12,  # picoseconds
        'n': 1e-9,   # nanoseconds  
        'u': 1e-6,   # microseconds
        'm': 1e-3,   # milliseconds
        'k': 1e3,    # kiloseconds (uncommon but possible)
        'meg': 1e6,  # megaseconds (uncommon)
        'g': 1e9,    # gigaseconds (uncommon)
        't': 1e12,   # teraseconds (uncommon)
    }
    
    # Default to seconds if no unit
    if time_str[-1].isdigit():
        return float(time_str)
    
    # Extract number and unit
    match = re.match(r'(\d+(?:\.\d+)?)([a-zA-Z]+)', time_str)
    if match:
        value = float(match.group(1))
        unit = match.group(2).lower()
        
        # Handle common unit abbreviations
        if unit in unit_multipliers:
            return value * unit_multipliers[unit]
        elif unit == 's':
            return value  # seconds
        else:
            print(f"Warning: Unknown time unit '{unit}' in '{time_str}', treating as seconds")
            return value
    else:
        # Fallback: try to parse as plain number
        try:
            return float(time_str)
        except ValueError:
            print(f"Warning: Could not parse time value '{time_str}', using 0")
            return 0.0



def pre_process_circuit(cir_num):
    
    
    category_num = find_cat_from_num(cir_num) 
    path_category = local_config.path_category_md + f"{category_num}.md"
    # or the cat_num is already known, so just +"4.md"
    category_str = file_utils.get_file_to_str(path_category)

    path_output_num = local_config.path_output + f"{cir_num}/"
    # circuit_string = get_full_circuit_string(cir_num)
    cir_path = local_config.path_dataset+f"{cir_num}/{cir_num}.cir"
    circuit_string = file_utils.get_file_to_str(cir_path)
    has_input = has_port_from_nl(circuit_string) #if opamp does not have, there is problem
    is_diff = has_port_from_nl(circuit_string, target_ports=["VOUT2"])
    circuit_string = modify_duplicate_component(circuit_string) # remove duplicate component names like 2 C1 in 167
    circuit_string = clean_netlist(circuit_string)# ADD .include here. remove (). nmos4' to 'nmos' and 'pmos4' to 'pmos'. REMOVE 'resistor' and 'capacitor'
    circuit_string = add_params(circuit_string) #ADD .param. ADD w,l,m to mos. ADD {value} for R and C
    circuit_string = add_DC_source(circuit_string)
    cat_json = file_utils.get_dict_from_json(local_config.path_category_jsons + f"{category_num}.json")
    netlist = add_control(circuit_string)
    file_utils.delete_all_files_except_dir(path_output_num)
    print("==cir_str\n", netlist)

    return path_output_num, category_num, category_str, netlist, has_input, is_diff, cat_json
# endregion modify



def make_path_id(spec_sims, path_output_num):
    struct_path_id = {}  # id: path
    # has_list_flag = False
    for spec_sim in spec_sims:
        path_file = path_output_num + spec_sim.sim_file_name
        if os.path.exists(path_file):
            # print(f"File {path_file} exists.")
            spec_num_id = spec_sim.spec_num_id
            target = struct_path_id.get(spec_num_id)
            if target is None:
                struct_path_id[spec_num_id] = path_file
            else:
                if not isinstance(target, list):
                    struct_path_id[spec_num_id] = [target, path_file]
                else:
                    struct_path_id[spec_num_id].append(path_file)
                # has_list_flag = True
        else:
            print(f"File {path_file} does not exist.")
            raise RuntimeError(f"Expected output file {path_file} not found.")
    
    # if has_list_flag:
    #     for key, paths in struct_path_id.items():
    #         if len(paths) == 1: 
    #             struct_path_id[key] = paths[0]
    # print(struct_path_id)
    # raise ValueError("test")
    return struct_path_id

def has_port_from_nl(netlist, target_ports = ["VIN1", "IIN1"]):
    
    for target_port in target_ports:
        pattern = rf"\b{target_port}\b"
        if re.search(pattern, netlist):
            return True
    return False

def are_ports_all_exist(path, target_ports=["VIN1"]):
    if os.path.isfile(path):
        with open(path, 'r') as f:
            content = f.read()
        for target_port in target_ports:
            pattern = rf"\b{target_port}\b"# \b ensures match of the whole word only
            
            if re.search(pattern, content):
                continue
            return False
        return True
# if 1 of theses exists, return True
def is_port_exist(path, target_ports=["VIN1"]):
    
    content = file_utils.get_file_to_str(path)
    # print("content\n",content)
    return has_port_from_nl(content, target_ports)
    
def is_cir_debugged(cir_num):
    path = local_config.path_output + f"{cir_num}/debug_metadata.json"
    try:
        if not os.path.isfile(path):
            return False
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # If retry_count exists and is not zero, consider it debugged
        retry = data.get('retry_count')
        if retry is None:
            return False
        try:
            return int(retry) != 0
        except Exception:
            # Non-integer retry value: fallback to truthiness
            return bool(retry)
    except Exception as e:
        print(f"is_cir_debugged: could not read '{path}': {e}")
        return False



def ensure_data_format_settings(netlist):
    """Ensure netlist contains required data format settings.
    
    Checks for 'set units=degrees' and 'set wr_vecnames'. If missing,
    adds them after the '.control' line.
    
    Args:
        netlist (str): The SPICE netlist content as a string.
        
    Returns:
        str: Modified netlist with settings added if necessary.
    """

    #0 replace \\n to \n when it is too long texts
    netlist = netlist.replace('\\n', '\n')
    # 1
    lines = netlist.split('\n')
    has_units = False
    has_wr_vecnames = False
    control_index = -1
    
    # Find .control line and check for existing settings
    for i, line in enumerate(lines):
        line_stripped = line.strip().lower()
        
        if line_stripped == '.control':
            control_index = i
        elif line_stripped == 'set units=degrees':
            has_units = True
        elif line_stripped == 'set wr_vecnames':
            has_wr_vecnames = True
    
    # If .control not found, return unchanged
    if control_index == -1:
        return netlist
    
    # If both settings present, return unchanged
    if has_units and has_wr_vecnames:
        return netlist
    
    # Add missing settings after .control
    insert_lines = []
    if not has_units:
        insert_lines.append('set units=degrees')
    if not has_wr_vecnames:
        insert_lines.append('set wr_vecnames')
    
    # Insert after .control line
    lines[control_index + 1:control_index + 1] = insert_lines
    
    return '\n'.join(lines)

def count_retry_info(cir_nums, json_name = "debug_metadata.json" ):
    total_retries = 0
    zero_retry_count = 0
    len_cir_nums = len(cir_nums)
    for cir_num in cir_nums:
        path = local_config.path_output + f"{cir_num}/" + json_name
        # print(path)
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
            retry = data.get("retry_count", -1)
            # print(f"Circuit {cir_num}: {retry} retries")
            if retry == 0:
                zero_retry_count +=1
            if retry == -1:
                raise ValueError(f"Invalid retry count in {path}")
            total_retries += retry
    avg_retry = total_retries / len_cir_nums if len_cir_nums > 0 else 0

    return total_retries, avg_retry, zero_retry_count


def reduce_duplicate_str(duplicate_str):
    # duplicate_str = "error: no such parameter res.\nerror: no such parameter res.\nerror: no such parameter res."
    # Collapse consecutive duplicate lines and annotate repetitions, e.g.
    # 'msg\nmsg\nmsg' -> 'msg (x3)'
    lines = duplicate_str.splitlines()
    if not lines:
        return ""

    out_lines = []
    prev = lines[0]
    count = 1
    max_count = 0
    for line in lines[1:]:
        if line == prev:
            count += 1
        else:
            if count > 1:
                out_lines.append(f"{prev} (x{count})")
            else:
                out_lines.append(prev)
            prev = line # update check line!!!
            max_count = max(max_count, count)
            count = 1

    # flush last
    if count > 1:
        out_lines.append(f"{prev} (x{count})")
    else:
        out_lines.append(prev)
    
    max_count = max(max_count, count)
    print(f"Maximum consecutive duplicates: {max_count}")
    
    reduced = "\n".join(out_lines)
    # print("Original:\n", duplicate_str)
    # print("Reduced:\n", reduced)
    return reduced

def get_biggest_rule_number(rules_list):
    numbers = []
    
    for rule in rules_list:
        # Match digits at the absolute start (^) of the string followed by a dot
        match = re.match(r"^(\d+)\.", rule.strip())
        if match:
            # Convert the matched string digit to an actual integer
            numbers.append(int(match.group(1)))
            
    # Return the maximum number found, or 0 if the list was empty
    return max(numbers) if numbers else 0

def get_netlist_diff(error_netlist: str, fixed_netlist: str, context_lines: int = 3) -> str:
    """
    Compares two netlists and returns a compact string showing only the differences
    plus a few lines of surrounding context.
    """
    # Split the netlists into lists of lines
    error_lines = error_netlist.splitlines()
    fixed_lines = fixed_netlist.splitlines()
    
    # Generate a unified diff (like git diff)
    diff = difflib.unified_diff(
        error_lines, 
        fixed_lines, 
        fromfile='error_netlist', 
        tofile='fixed_netlist',
        n=context_lines,  # Number of context lines to show around changes
        lineterm=''
    )
    
    # Join the diff generator into a single string
    diff_string = "\n".join(diff)
    
    # If there are absolutely no differences, return a note
    if not diff_string:
        return "No differences found between the netlists."
        
    return diff_string


def test_delay(sec, msg = ""):
    print(f"{msg}: Waited for {sec} seconds")
    time.sleep(sec)

