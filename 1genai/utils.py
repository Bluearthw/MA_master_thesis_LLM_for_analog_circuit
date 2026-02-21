import re
import time
import os
import itertools
DEFAULT_W = "0.5u"
DEFAULT_L = "90n"
DEFAULT_M = "1"
DEFAULT_R = "1k"
DEFAULT_C = "3p"
##### for pyspice
from PySpice.Spice.NgSpice.Shared import NgSpiceShared
import matplotlib.pyplot as plt
import numpy as np
import local_config
from google import genai

def get_client():
    return genai.Client(api_key=local_config.GOOGLE_API_KEY)
# region for file IO
def get_file_to_str(path, str="",):
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
    for target_port in target_ports:
        pattern = rf"\b{target_port}\b"# \b ensures match of the whole word only
        
        if re.search(pattern, content):
            return True
    return False
    
        

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

def find_num_by_port_name(dataset_path,port_name=["VB1"],num_range = list(range(4,1045))):
    exist_nums = []
    for i in num_range: #4 to 1144
        if os.path.isfile(dataset_path):
            path_nl = dataset_path + f"/{i}/{i}.cir"
            if is_port_exist(path_nl,port_name):

                    exist_nums.append(i)
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
    difference = list(set(nums_big).difference(set(nums2)))
    print("# ", len(difference))
    print(sorted(difference))

def find_cir_without_pattern_from_1044cir(dataset_path,name_to_check,nums = list(range(4,1045))):
    i = 4
    exist_nums = []
    for i in nums:

        path_nl = dataset_path + f"/{i}/{i}.cir"
        if os.path.isfile(path_nl):
            # let's check cir file first, only when it has vin
        
            if not is_port_exist(path_nl,name_to_check):
                exist_nums.append(i)
            # counter part
    return exist_nums

def find_cir_with_pattern_from_1044cir(dataset_path,name_to_check):
    i = 4
    exist_nums = []
    while True:

        path_nl = dataset_path + f"/{i}/{i}.cir"
        if os.path.isfile(path_nl):
            # let's check cir file first, only when it has vin
        
            if is_port_exist(path_nl,name_to_check):
                exist_nums.append(i)
            # counter part
        i+=1
        if i > 1044:
            break
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



def find_correct_RF_from_num_with_agent(dataset_path, nums = []):
    nums = local_config.num_SISO_RF_before_filtered 

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

    return '\n.include "1genai/data/45nm.sp"\n' + netlist


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
    output = []
    output.append("*params ")
    output.extend(param_statements)
    output.extend(modified_lines)

    return "\n".join(output)


def add_DC_source(netlist, vdd="1.2", vb1="0.7"):
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
    param_vb1_line = f"\n.param VB1={vb1}"

    # Standard source definitions using the parameter
    vdd_source = "\nvdd VDD 0 dc=VDD"
    vss_source = "\nvss VSS 0 dc=0"  # VSS is typically ground reference
    vb1_source = "\nvb1 VB1 0 dc=VB1"  # VSS is typically ground reference

    # source_block = f"\n{param_line}\n{vdd_source}\n"
    # vss_block = f"{vss_source}\n"
    # --- 2. Check for Node Usage ---

    # This regex looks for VDD or VSS surrounded by word boundaries (\b),
    # ensuring it's not part of a longer word (like 'VSS_test').
    # We use re.DOTALL to search across multiple lines.
    vdd_in_use = re.search(r"\bVDD\b", netlist, re.IGNORECASE)
    vss_in_use = re.search(r"\bVSS\b", netlist, re.IGNORECASE)
    vb_in_use = re.search(r"\bVB1\b", netlist, re.IGNORECASE)

    # --- 3. Determine Insertion Point and Insert ---

    if vdd_in_use:
        insertion_point = 0

        for i, line in enumerate(netlist.splitlines()):
            line_stripped = line.strip()

            if line_stripped and (
                line_stripped[0].isalpha() or line_stripped.startswith(".")
            ):
                insertion_point = i
                break

        lines = netlist.splitlines()

        # Insert the source block at the determined point
        # We replace the line at insertion_point with itself + the new block
        lines.insert(insertion_point, param_line)

        lines.insert(len(lines), vdd_source)
        if vb_in_use:
            lines.insert(insertion_point, param_vb1_line)
            lines.insert(len(lines), vb1_source)

        if vss_in_use:

            lines.insert(len(lines), vss_source)

        return "\n".join(lines)

    else:
        print("VDD and VSS nodes not found in netlist. Skipping DC source addition.")
        return netlist


def add_C_load(netlist, node="vout1", Cload="10p"):
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


# endregion


# region for modifying
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


# endregion


# region for pyspice
def get_vector_and_make_array(plot, name):
    array = np.array(plot[name]._data)
    # array = np.array(vec.array)
    return array


def pyspice_op_sim(circuit, node="vout1"):
    ngspice = NgSpiceShared.new_instance()
    ngspice.load_circuit(circuit)
    ngspice.run()
    # plot = ngspice.plot(simulation=None, plot_name="op1")# ngspice.last_plot
    plot = ngspice.plot(
        simulation=None, plot_name=ngspice.last_plot
    )  # ngspice.last_plot
    # print('Plots:\n', ngspice.plot_names)
    print('plot?\n',plot)
    vout = get_vector_and_make_array(plot, node)
    net2 = get_vector_and_make_array(plot, "net2")
    print("==net2\n",net2)

    
    # .param VINCM=0.53
    # .param VB1=0.45
    # * in this way Vout1 is 0.61 1/2 VDD
    # ==pyspice_op_sim (array([0.61209825]), array([1.2]), array([1.2]), array([5.2854921e-12]), array([6.19755257e-13]))
    #    others seem useless
    # 'vin1': variable: vin1 voltage, 'vdd': variable: vdd voltage, 'vb1': variable: vb1 voltage, 'vout1': variable: vout1 voltage}
    return vout


# endregion


def test_delay(sec):
    time.sleep(sec)
