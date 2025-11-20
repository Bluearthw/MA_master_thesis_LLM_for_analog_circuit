from google import genai
from local_config import GOOGLE_API_KEY
import re

DEFAULT_W = "0.5u"
DEFAULT_L = "90n"
DEFAULT_M = "1"
DEFAULT_R = "1k"
DEFAULT_C = "3p"


def get_client():
    client = genai.Client(api_key=GOOGLE_API_KEY)
    return client


def get_file_to_str(path, str ):
    try:
        with open(path, "r", encoding="utf-8") as f:
            circuit_string = str + f.read()
            # print(f"Circuit loaded successfully from: {cir_path}")
            return circuit_string
    except FileNotFoundError:
        print(f"Error: no files at: {path}")


def check_file_and_overwrite(path, msg):
    with open(f"{path}", "w") as f:
        f.write(f"{msg}")


def clean_netlist(netlist):
    """
    Cleans an analog SPICE netlist string by standardizing component names and removing 
    descriptive text.

    Performs the following transformations on the input netlist string:
    1. Removes all parentheses '(', ')'.
    2. Renames the device model 'nmos4' to 'nmos' and 'pmos4' to 'pmos'.
    3. Removes the descriptive words 'resistor' and 'capacitor' and replaces them 
       with a newline character, effectively removing them from the component definition line.

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

    return netlist


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


def add_params(netlist): # input should be lines here
    param_statements = []
    modified_lines = []
    transistor_ids = []
    resistor_ids_processed = set()
    capacitor_ids_processed = set()
    m_line_pattern = re.compile(r"^(M\S+)\s+(.+?)$", re.IGNORECASE)
    """
    [RC], either 'R' or 'C'
    \Rs+, match 1 more which is not white space
    """
    rc_line_pattern = re.compile(r"^([RC]\S+)\s+(\S+)\s+(\S+)$", re.IGNORECASE)
    digit_extractor = re.compile(r"\d+")
    for line in netlist:
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
def add_DC_source(netlist, vdd='1.2'):

    # isUsed = re.search(r'\bVDD\b', circuit_string, re.IGNORECASE)
    param_line = f"\n.param VDD={vdd}"
    
    # Standard source definitions using the parameter
    vdd_source = "\nVdd VDD 0 dc=VDD"
    vss_source = "\nVss VSS 0 dc=0"  # VSS is typically ground reference
    
    # source_block = f"\n{param_line}\n{vdd_source}\n"
    # vss_block = f"{vss_source}\n"
    # --- 2. Check for Node Usage ---
    
    # This regex looks for VDD or VSS surrounded by word boundaries (\b),
    # ensuring it's not part of a longer word (like 'VSS_test').
    # We use re.DOTALL to search across multiple lines.
    vdd_in_use = re.search(r'\bVDD\b', netlist, re.IGNORECASE)
    vss_in_use = re.search(r'\bVSS\b', netlist, re.IGNORECASE)

    # --- 3. Determine Insertion Point and Insert ---
    
    if vdd_in_use:
        insertion_point = 0
        
        for i, line in enumerate(netlist.splitlines()):
            line_stripped = line.strip()
            
            if line_stripped and (line_stripped[0].isalpha() or line_stripped.startswith('.')):
                insertion_point = i
                break
        
        lines = netlist.splitlines()
        
        # Insert the source block at the determined point
        # We replace the line at insertion_point with itself + the new block
        lines.insert(insertion_point, param_line)
        lines.insert(len(lines), vdd_source)
        if vss_in_use:
            
            lines.insert(len(lines), vss_source)
        
        return '\n'.join(lines)
        
    else:
        print("VDD and VSS nodes not found in netlist. Skipping DC source addition.")
        return netlist