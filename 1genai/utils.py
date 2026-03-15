import re
import time
import os
import pandas as pd
import subprocess
import io
import contextlib
import numpy as np
import scipy.interpolate as interp
import scipy.optimize as sciopt
from PySpice.Spice.NgSpice.Shared import NgSpiceShared
import matplotlib.pyplot as plt
from google import genai
from scipy.integrate import trapezoid

##### local
import local_config
DEFAULT_W = "0.5u"
DEFAULT_L = "90n"
DEFAULT_M = "1"
DEFAULT_R = "1k"
DEFAULT_C = "3p"

def get_client():
    return genai.Client(api_key=local_config.GOOGLE_API_KEY_yong)

# region for file IO
def get_file_to_str(path, str=""):
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as file: # https://www.geeksforgeeks.org/python/read-file-as-string-in-python/
                
                circuit_string = file.read() 
                    
                if len(str) > 0:
                    circuit_string = str + circuit_string
                # print(f"Circuit loaded successfully from: {cir_path}")
                return circuit_string
                
        except FileNotFoundError:
            print(f"Error: no files at: {path}")
            raise FileNotFoundError(" No File")
        
def get_file_to_lines(path, n_line, start_from_end = False):
    if os.path.isfile(path):
        lines = []
        try:
            with open(path, "r", encoding="utf-8") as file: 
                if start_from_end: # .remove("\n")
                    lines = file.readlines()[-n_line:]
                    # lines.remove('\n') # it removes only 1

                else:
                    lines = file.readlines()[:n_line]
                return lines
                ##################
                # don't use your own function, very slow #
                ###########################
                # line = file.readline()
                # counter = 0
                # while line:
                #     lines.append(line)
                #     line = file.readline()
                #     counter += 1
                #     if counter > n_line:
                #         return lines
                
        except FileNotFoundError:
            print(f"Error: no files at: {path}")
            raise FileNotFoundError(" No File")            
    return []       

def check_file_and_overwrite(path, msg):
    with open(f"{path}", "w") as file:
        file.write(f"{msg}")

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
    with open(path, 'r') as f:
        content = f.read()
    print("content\n",content)
    for target_port in target_ports:
        pattern = rf"\b{target_port}\b"# \b ensures match of the whole word only
        
        if re.search(pattern, content):
            return True
    return False
    
def delete_all_files_skip_dir(folder_path):
    """
    Deletes all files in the specified folder.
    Does not remove subdirectories or the folder itself.
    """
    # Validate folder path
    if not os.path.exists(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        return
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a directory.")
        return

    deleted_count = 0
    failed_count = 0

    # Iterate over all items in the folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Only delete files, skip directories!!!!!
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                print(f"Failed to delete '{file_path}': {e}")
                failed_count += 1

    print(f"Deleted {deleted_count} file(s).")
    if failed_count > 0:
        print(f"Failed to delete {failed_count} file(s).")        

def save_str_to_file(str, path = local_config.path_output + "final_netlist.cir"):
    with open(path, "w") as f:
        f.write(str)
# endregion for file IO


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
                lines = get_file_to_lines(path, lines_to_read)
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
    lines = get_file_to_lines(path_exaplain,10,True)
    
    for line in lines:
        if "RF" in line:
            return True
    lines2 = get_file_to_lines(path_exaplain,8)
    string = "".join(lines2)
    if "RF" in string:
        # end_time = time.perf_counter()
        # print("time used",end_time-start_time)
        return True

    return False

def find_ports_from_all(dataset_path,nums = list(range(4,1045))):
    
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
        if int(get_file_to_str(path)) == class_id:
            exist_nums.append(i)
            # counter part
        
    return exist_nums

def find_cat_from_num(num):
    path = local_config.path_classified_dataset+ f"/{num}/detected_class.txt"
    return int(get_file_to_str(path))
# endregion for classification



# region for adding (tool)
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

        # --- Generate Parameter Names ---
        w_param = f"w{num_id}"
        l_param = f"l{num_id}"
        m_param = f"m{num_id}"

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
        new_m_line = (
            f"{transistor_id} {nodes_and_model} w={w_param} l={l_param} m={m_param}"
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
    m_line_pattern = re.compile(r"^(M\S+)\s+(.+?)$", re.IGNORECASE)
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
    param_line = f"\n.param VDD={vdd}"
    param_line_vb1 = f"\n.param VB1={vb1}"
    param_line_ib1 = f"\n.param IB1={ib1}"

    # Standard source definitions using the parameter
    vdd_source = "\nvdd VDD 0 dc=VDD"
    vss_source = "\nvss VSS 0 dc=0"  # VSS is typically ground reference
    vb1_source = "\nvb1 VB1 0 dc=VB1"  # VSS is typically ground reference
    ib1_source = "\nib1 IB1 0 dc=IB1"  # VSS is typically ground reference

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


# endregion modify


# region for pyspice
def get_vector_and_make_array(plot, name):

    array = np.array(plot[name]._data)
    # array = np.array(vec.array)
    return array

def pyspice_op_sim_simple(circuit, node="vout1"):
    try:
        ngspice = NgSpiceShared.new_instance()
        ngspice.load_circuit(circuit)
        ngspice.run()
        print("simple :: Simulation completed successfully.")
    except Exception as e:
        print(f'Exception: {e}')


def pyspice_op_sim(circuit, node="vout1"):

    
    # Capture both stdout and stderr to detect ngspice errors
    stdout_capture = io.StringIO()
    try:
        ngspice = NgSpiceShared.new_instance()
        
        # Redirect both stdout and stderr to capture any messages
        with contextlib.redirect_stdout(stdout_capture):
            ngspice.load_circuit(circuit)
            ngspice.run()
        
        # Check for errors in captured output
        stdout_output = stdout_capture.getvalue()
        combined_output = stdout_output 
        
        # Check for various error indicators (case-insensitive)
        error_keywords = ["error", "no such", "command available", "illegal", "bad", "unable", "failed"]
        for keyword in error_keywords:
            if keyword.lower() in combined_output.lower():
                return {"success": False, "message": combined_output.strip()}
        
        # Also check stdout from ngspice object
        ngspice_stdout = ngspice.stdout if hasattr(ngspice, 'stdout') else ""
        for keyword in error_keywords:
            if keyword.lower() in ngspice_stdout.lower():
                return {"success": False, "message": ngspice_stdout.strip()}
        
        return {"success": True, "message": "Simulation OK"}
    except Exception as e:
        stdout_output = stdout_capture.getvalue()
        error_msg = (stdout_output).strip() if stdout_output else str(e)
        return {"success": False, "message": error_msg}
    finally:
        stdout_capture.close()

def pyspice_op_sim_final(circuit):
    pyspice_op_sim_simple(circuit)
    delete_all_files_skip_dir(local_config.path_output)
    # Use a single string buffer for all stdout/stderr
    log_capture = io.StringIO()
    
    try:
        ngspice = NgSpiceShared.new_instance()
        
        with contextlib.redirect_stdout(log_capture), contextlib.redirect_stderr(log_capture):
            ngspice.load_circuit(circuit)
            ngspice.run()
        
        # NgSpice often stores the last output in its own internal stdout
        output_log = log_capture.getvalue().strip()
        # Filter out known benign gmin-stepping chatter (reduces spam in output)
        filtered_lines = []
        for line in output_log.splitlines():
            low = line.lower()
            if "trying" in low:
                continue

            # Keep other notes; only remove gmin-stepping noise
            filtered_lines.append(line)
        output_log = "\n".join(filtered_lines).strip()

        print("====NgSpice Output Log:\n", output_log)
        # Logic: If the log contains common failure signatures 
        # OR if the simulation didn't produce expected results
        if any(err in output_log.lower() for err in ["error", "failed", "no such command", "warning"]):
            return {"success": False, "message": output_log}

        return {"success": True, "message": "Simulation OK\n" + output_log}

    except Exception as e:
        return {"success": False, "message": f"Python Exception: {str(e)}"}
    finally:
        log_capture.close()

def run_ngspice_direct(netlist_content, is_save = True, path_nl = local_config.path_output +  "4/final_netlist.cir"):
    # 1. Save netlist to a temporary file
    if is_save:
        path_nl = "./1genai/output/temp_circuit.cir"
        with open(path_nl, "w") as f:
            f.write(netlist_content)
        
    path_ngspice = r'D:/1kulStudy/8MA_Thesis/tool/Spice64/bin/ngspice_con.exe'  # Update this path to your ngspice executable

    #output log stdout is not useful
    try:
        process = subprocess.run(
            [path_ngspice, "-b", "-n", path_nl],
            capture_output=True,
            text=True,
            shell=False,
        )
        
        # Combine stdout and stderr for analysis
        logs = process.stderr if process.stderr and process.stderr.strip() else ""
        

        if logs:
            print("--- Simulation Log (stderr) ---")
            print(logs)
        error_log_lower = logs.lower()
        
        # Determine if this is a real error or just a warning
        # Check for fatal errors
        has_fatal_error = "fatal error" in   error_log_lower
        has_error = "no such" in error_log_lower or "error" in error_log_lower or "warning" in error_log_lower 
        # Exclude the "dc value used for op" warning - it's not a real error
        is_dc_value_warning = "note" in error_log_lower

        filtered_lines = [
            line for line in error_log_lower.splitlines() 
            if not line.strip().lower().startswith("note:")
        ]
        clean_log = "\n".join(filtered_lines)

        # If there's a fatal error, check error details even if exit code is 0
        if has_fatal_error:
            # print(f"--- FATAL ERROR DETECTED ---")
            print(f"Error Details: {logs}")
            return {"success": False, "message": f"Simulation failed\n{logs}"}
        
        print(f"=== Simulation Analysis ---{is_dc_value_warning}, fatal {has_fatal_error}")
        # If only a dc value warning (no fatal error), treat as success
        if has_error:
            # print("--- Simulation completed with warnings (non-fatal) ---")
            return {"success": False, "message": clean_log}
        if is_dc_value_warning:
            # print("--- Simulation completed with warnings (non-fatal) ---")
            return {"success": True, "message": f"Simulation OK\n{logs}"}
        
        # Check exit code for crash #????? never see 0
        if process.returncode != 0:
            print(f"--- CRASH DETECTED (Exit Code: {process.returncode}) ---")
            error_msg = logs if logs else "Segmentation Violation (Hard Crash)"
            print(f"Error Details: {error_msg}")
            return {"success": False, "message": f"Simulation failed (Exit Code: {process.returncode})\n{error_msg}"}
        
        # Normal success case
        return {"success": True, "message": f"Simulation OK\n{logs}"}
        
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "Simulation timed out"}

# endregion pyspice

# region measurement
class SpiceResult:
    def __init__(self, path_gain, path_psrr, path_noise, path_trans):
        # gain data
        self.path = path_gain
        data_gain = np.genfromtxt(path_gain, autostrip=True, skip_header=1)
        self.freq = data_gain[:, 0]
        # store gain as complex and compute magnitude/phase
        self.vout_complex = data_gain[:, 1] + 1j * data_gain[:, 2]
        self.mag = np.abs(self.vout_complex)
        self.mag_db = 20 * np.log10(self.mag)
        self.phase = np.angle(self.vout_complex, deg=True)

        # psrr data (same format as gain files)
        self.path_psrr = path_psrr
        self.path_noise = path_noise
        self.path_trans = path_trans
        

    def get_dc_gain(self):
        """Returns the magnitude at the lowest frequency."""
        return self.mag[0]
    
    def get_max_gain(self):
        """Returns the maximum gain in dB."""
        return np.max(self.mag_db)
    def get_bandwidth(self):
        """Finds the -3dB cutoff frequency."""
        
        length = len(self.mag_db)
        last_mag_db =  np.mean(self.mag_db[int(length*0.7) : -1])
        first_mag_db = np.mean(self.mag_db[0 : int(length*0.3)])
        if last_mag_db < first_mag_db: 
        # LP
            target = self.mag_db[0] - 3
            bw, found = get_best_crossing(self.freq, self.mag_db, target)
            return bw if found else 0
        else:#HP
            target = self.mag_db[-1] - 3
            bw, found = get_best_crossing(self.freq, self.mag_db, target)
            return self.freq[-1] - bw if found else 0
    def get_unity_gain_bw(self):
        """Finds the frequency where gain is 0dB."""
        ugbw, found = get_best_crossing(self.freq, self.mag_db, 0)
        return ugbw if found else None
    def get_ugbw(self):
        
        ac_mag = self.mag_db
        ac_cross, ac_found = get_best_crossing(self.freq,ac_mag,0)
        if not ac_found:
            return 0
        # print(f"ugbw: {ac_cross}\n")
        return ac_cross
    def get_phm(self):# assumed LP!!!

        ugbw = self.get_ugbw()
        if ugbw <= np.min(self.freq) or ugbw >= np.max(self.freq) or ugbw == 0:
            print("Warning: UGBW out of interpolation range or not found")
            return 0
        phi_deg = np.unwrap(np.angle(self.vout_complex))*180/np.pi
        phi_interpolate = interp.interp1d(self.freq,phi_deg)
        phi_ugbw = phi_interpolate(ugbw)

        phm = 180 + phi_ugbw
        # print(f"phm: {phm}\n")
        
        return phm
    
    def get_gain_margin(self):
        """
        Calculates the gain margin (in dB).
        Gain margin is the gain at the phase crossover frequency (where phase = -180°).
        """
        phi_deg = np.unwrap(np.angle(self.vout_complex)) * 180 / np.pi
        
        # Find the frequency where phase crosses -180 degrees
        target_phase = -180
        
        try:
            phi_interpolate = interp.interp1d(self.freq, phi_deg)
            mag_db_interpolate = interp.interp1d(self.freq, self.mag_db)
            
            def phase_error(f):
                return phi_interpolate(f) - target_phase
            
            # Find the crossing frequency where phase = -180°
            xstart, xstop = self.freq[0], self.freq[-1]
            phase_crossover_freq = sciopt.brentq(phase_error, xstart, xstop)
            
            # Get the gain at the phase crossover frequency
            gain_at_crossing = mag_db_interpolate(phase_crossover_freq)
            
            # Gain margin is -gain (in dB) at the phase crossover frequency
            # Positive gain margin means stable system
            gain_margin = -gain_at_crossing
            
            return gain_margin
        except ValueError:
            # Phase never crosses -180 degrees
            print("Warning: Phase does not cross -180 degrees in the frequency range")
            return 0

    # ----- new PSRR helpers -----
    def get_psrr(self): # maybe it can be interpolated to get more precise value
        """Return arrays (frequency, psrr_db) from the parsed PSRR file."""
        data_psrr = np.genfromtxt(self.path_psrr, autostrip=True, skip_header=1)
        psrr_complex = data_psrr[:, 1] + 1j * data_psrr[:, 2]
        psrr_mag = np.abs(psrr_complex)
        max = np.max(psrr_mag)
        min = np.min(psrr_mag)
        # psrr in dB (positive numbers indicate better rejection)
        self.psrr_db = 20 * np.log10(1/(max - min)) # avoid division by zero
        return self.psrr_db
    def get_in_equivalent_noise_from_total(self): # there is another vector that might calculate the integrated noise, 
        data_noise = np.genfromtxt(self.path_noise, autostrip=True, skip_header=1)
        # this is total so just skip output, and head is skipped.
        return data_noise[1] 
        
    def get_in_equivalent_noise_from_spectrum(self): # there is another vector that might calculate the integrated noise, 
        data_noise = np.genfromtxt(self.path_noise, autostrip=True, skip_header=1)
        #0,2 are f, 1 is onoise, 3 is inoise
        inoise = data_noise[:, 1] 
        # 2. Square the noise to get V^2/Hz (Power Density)
        noise_power_density = inoise**2
        
        # 3. Integrate over frequency
        f_range = data_noise[:, 0] # frequency range
        total_variance = trapezoid(noise_power_density, f_range)
        
        # 4. Take the square root to get back to RMS Volts
        return np.sqrt(total_variance)
    def get_slew_rate(self, threshold_low=0.1, threshold_high=0.9): # there is another vector that might calculate the integrated noise, 
        data_trans = np.genfromtxt(self.path_trans, autostrip=True, skip_header=1)
        vout_tran = data_trans[:, 1] #  vout is the second column
        time = data_trans[:, 0] #  time is the first column

        vmin = np.min(vout_tran)
        vmax = np.max(vout_tran)
        print(f"vmin: {vmin}, vmax: {vmax}")
        vlo = vmin + threshold_low*(vmax-vmin)
        vhi = vmin + threshold_high*(vmax-vmin)

        slew_ary = []
        for i in range(4,len(vout_tran)-4):
            if vout_tran[i-1] < vlo <= vout_tran[i]:
                for j in range(i, len(vout_tran)-4):   # cam i use pointers in python??? check later for higher search efficiency
                    if vout_tran[j-1] < vhi <= vout_tran[j]:
                        # print("time range",time[i-4:j+4])
                        t_r1, found_r1 = get_best_crossing(time[i-4:j+4], vout_tran[i-4:j+4], vlo)
                        t_r2, found_r2 = get_best_crossing(time[i-4:j+4], vout_tran[i-4:j+4], vhi)
                        if found_r1 and found_r2: #
                            slew_ary.append((vhi - vlo) / (t_r2 - t_r1))
                            i=j
                        break
        if not slew_ary:
            print("Warning: Not Slew Rate")
            return 0
        mean = np.mean(slew_ary)*1e-6
        return mean
class SpiceResultNew:
    def __init__(self):
        # paths
        self.path_ac_gain = ""
        self.path_psrr = ""
        self.path_noise = ""
        self.path_trans = ""

        self.freq = 0
        # store gain as complex and compute magnitude/phase
        self.vout_complex = []
        self.mag = []
        self.mag_db = []
        self.phase = []

        self.psrr_db = 0

        self.data_trans = []

        
        
    def load_ac_gain_data(self, path_gain):
        self.path_ac_gain = path_gain
        data_gain = np.genfromtxt(path_gain, autostrip=True, skip_header=1)
        self.freq = data_gain[:, 0]
        # store gain as complex and compute magnitude/phase
        self.vout_complex = data_gain[:, 1] + 1j * data_gain[:, 2]
        self.mag = np.abs(self.vout_complex)
        self.mag_db = 20 * np.log10(self.mag)
        self.phase = np.angle(self.vout_complex, deg=True)

    def get_dc_gain(self, path_gain):
        """Returns the magnitude at the lowest frequency."""
        if self.path_ac_gain == "":
            self.load_ac_gain_data(path_gain)

        return self.mag[0]
    
    def get_bandwidth(self):
        """Finds the -3dB cutoff frequency."""
        
        length = len(self.mag_db)
        last_mag_db =  np.mean(self.mag_db[int(length*0.7) : -1])
        first_mag_db = np.mean(self.mag_db[0 : int(length*0.3)])
        if last_mag_db < first_mag_db: 
        # LP
            target = self.mag_db[0] - 3
            bw, found = get_best_crossing(self.freq, self.mag_db, target)
            return bw if found else 0
        else:#HP
            target = self.mag_db[-1] - 3
            bw, found = get_best_crossing(self.freq, self.mag_db, target)
            return self.freq[-1] - bw if found else 0
    
    def get_psrr(self,path_psrr): # maybe it can be interpolated to get more precise value
        """Return arrays (frequency, psrr_db) from the parsed PSRR file."""
        if self.path_psrr == "":
            self.path_psrr = path_psrr
            data_psrr = np.genfromtxt(path_psrr, autostrip=True, skip_header=1)
            psrr_gain_complex = data_psrr[:, 1] + 1j * data_psrr[:, 2]
            psrr_gain_mag = np.abs(psrr_gain_complex)
            psrr = self.mag / psrr_gain_mag            
        return psrr
    
    def get_max_gain(self, path_gain):
        """Returns the maximum gain in dB."""
        if self.path_ac_gain == "":
            self.load_ac_gain_data(path_gain)
        return np.max(self.mag_db)
    def get_unity_gain_bw(self):
        """Finds the frequency where gain is 0dB."""
        ugbw, found = get_best_crossing(self.freq, self.mag_db, 0)
        return ugbw if found else None
    def get_ugbw(self):
        
        ac_mag = self.mag_db
        ac_cross, ac_found = get_best_crossing(self.freq,ac_mag,0)
        if not ac_found:
            return 0
        # print(f"ugbw: {ac_cross}\n")
        return ac_cross
    def get_phm(self):# assumed LP!!!

        ugbw = self.get_ugbw()
        if ugbw <= np.min(self.freq) or ugbw >= np.max(self.freq) or ugbw == 0:
            print("Warning: UGBW out of interpolation range or not found")
            return 0
        phi_deg = np.unwrap(np.angle(self.vout_complex))*180/np.pi
        phi_interpolate = interp.interp1d(self.freq,phi_deg)
        phi_ugbw = phi_interpolate(ugbw)

        phm = 180 + phi_ugbw
        # print(f"phm: {phm}\n")
        
        return phm
    
    def get_gain_margin(self,path_gain):
        """
        Calculates the gain margin (in dB).
        Gain margin is the gain at the phase crossover frequency (where phase = -180°).
        """
        if self.path_ac_gain == "":
            self.load_ac_gain_data(path_gain)
            
            
        phi_deg = np.unwrap(np.angle(self.vout_complex)) * 180 / np.pi
        
        # Find the frequency where phase crosses -180 degrees
        target_phase = -180
        
        try:
            phi_interpolate = interp.interp1d(self.freq, phi_deg)
            mag_db_interpolate = interp.interp1d(self.freq, self.mag_db)
            
            def phase_error(f):
                return phi_interpolate(f) - target_phase
            
            # Find the crossing frequency where phase = -180°
            xstart, xstop = self.freq[0], self.freq[-1]
            phase_crossover_freq = sciopt.brentq(phase_error, xstart, xstop)
            
            # Get the gain at the phase crossover frequency
            gain_at_crossing = mag_db_interpolate(phase_crossover_freq)
            
            # Gain margin is -gain (in dB) at the phase crossover frequency
            # Positive gain margin means stable system
            gain_margin = -gain_at_crossing
            
            return gain_margin
        except ValueError:
            # Phase never crosses -180 degrees
            print("Warning: Phase does not cross -180 degrees in the frequency range")
            return 0

    # ----- new PSRR helpers -----
    
    def get_in_equivalent_noise_from_total(self,path): # there is another vector that might calculate the integrated noise, 
        
        data_noise = np.genfromtxt(path, autostrip=True, skip_header=1)
        # this is total so just skip output, and head is skipped.
        return data_noise[1] 
        
    def get_in_equivalent_noise_from_spectrum(self,path): # there is another vector that might calculate the integrated noise, 
        data_noise = np.genfromtxt(path, autostrip=True, skip_header=1)
        #0,2 are f, 1 is onoise, 3 is inoise
        inoise = data_noise[:, 1] 
        # 2. Square the noise to get V^2/Hz (Power Density)
        noise_power_density = inoise**2
        
        # 3. Integrate over frequency
        f_range = data_noise[:, 0] # frequency range
        total_variance = trapezoid(noise_power_density, f_range)
        
        # 4. Take the square root to get back to RMS Volts
        return np.sqrt(total_variance)
    
    def get_slew_rate(self, path, threshold_low=0.1, threshold_high=0.9): # there is another vector that might calculate the integrated noise, 
        if self.path_trans == "":
            self.path_trans = path
            data_trans = np.genfromtxt(path, autostrip=True, skip_header=1)
            self.data_trans = data_trans
        vout_tran = self.data_trans[:, 1] #  vout is the second column
        time = self.data_trans[:, 0] #  time is the first column

        vmin = np.min(vout_tran)
        vmax = np.max(vout_tran)
        print(f"vmin: {vmin}, vmax: {vmax}")
        vlo = vmin + threshold_low*(vmax-vmin)
        vhi = vmin + threshold_high*(vmax-vmin)

        slew_ary = []
        for i in range(4,len(vout_tran)-4):
            if vout_tran[i-1] < vlo <= vout_tran[i]:
                for j in range(i, len(vout_tran)-4):   # cam i use pointers in python??? check later for higher search efficiency
                    if vout_tran[j-1] < vhi <= vout_tran[j]:
                        # print("time range",time[i-4:j+4])
                        t_r1, found_r1 = get_best_crossing(time[i-4:j+4], vout_tran[i-4:j+4], vlo)
                        t_r2, found_r2 = get_best_crossing(time[i-4:j+4], vout_tran[i-4:j+4], vhi)
                        if found_r1 and found_r2: #
                            slew_ary.append((vhi - vlo) / (t_r2 - t_r1))
                            i=j
                        break
        if not slew_ary:
            print("Warning: Not Slew Rate")
            return 0
        mean = np.mean(slew_ary)*1e-6
        return mean

    
def get_best_crossing(xvec, yvec, val):
        interp_fun = interp.InterpolatedUnivariateSpline(xvec, yvec)

        def fzero(x):
            return interp_fun(x) - val

        xstart, xstop = xvec[0], xvec[-1]
        try:
            return sciopt.brentq(fzero, xstart, xstop), True
        except ValueError:
            return xstop, False

# endregion for measurement


# region for class


# endregion for class
def test_delay(sec):
    time.sleep(sec)
    print(f"Waited for {sec} seconds")
