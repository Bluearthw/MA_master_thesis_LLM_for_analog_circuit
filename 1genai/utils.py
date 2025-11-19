from google import genai
from local_config import GOOGLE_API_KEY
import re

DEFAULT_W = "0.5u"
DEFAULT_L = "90n"
DEFAULT_M = "1"

def get_client():
    client = genai.Client(api_key = GOOGLE_API_KEY)
    return client

def get_file_to_str(path, str, str2=""):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            circuit_string = str + str2 + f.read() 
        # print(f"Circuit loaded successfully from: {cir_path}")
            return circuit_string
    except FileNotFoundError:    
        print(f"Error: no files at: {path}")

def check_file_and_overwrite(path, msg):
    with open(f"{path}", "w") as f:
        f.write(f"{msg}")

def clean_netlist(netlist):
    netlist = netlist.strip()

    netlist = re.sub(r'[()]', '', netlist)

    netlist = re.sub(r'\bnmos4\b', 'nmos', netlist)
    netlist = re.sub(r'\bpmos4\b', 'pmos', netlist)
    netlist = re.sub(r'\s*resistor\s*', '\n', netlist, flags=re.IGNORECASE)
    netlist = re.sub(r'\s*capacitor\s*', '\n', netlist, flags=re.IGNORECASE)
    
    return netlist

def add_params(netlist):
    param_statements = []
    modified_lines = []
    transistor_ids = []
    m_line_pattern = re.compile(r"^(M\S+)\s+(.+?)$", re.IGNORECASE)
    for line in netlist:
        line = line.strip()
        # print("line", line)
        #skip empty lines and comments
        if not line or line.startswith('*') or line.startswith('.'):
            modified_lines.append(line)
            continue
        match = m_line_pattern.match(line)
        if match:
            # Found an M-line
            transistor_id = match.group(1) # e.g., M1
            nodes_and_model = match.group(2) # e.g., VOUT2 VIN2 IB1 VSS nmos
            
            # Extract the numerical part of the ID for parameter naming (e.g., 1 from M1)
            # This makes the parameters w1, l1, m1
            try:
                # Use re.findall to safely extract all digits from the ID
                num_id = "".join(re.findall(r'\d+', transistor_id))
            except:
                # Fallback if no number is found (e.g., if ID is M_core)
                num_id = transistor_id.replace('M', '_')
            
            # --- Generate Parameter Names ---
            w_param = f"w{num_id}"
            l_param = f"l{num_id}"
            m_param = f"m{num_id}"
            
            # --- Create .param statement ---
            param_line = f".param {w_param}={DEFAULT_W} {l_param}={DEFAULT_L} {m_param}={DEFAULT_M}"
            
            # Only add if we haven't processed this transistor number yet
            # (Important for files with comments or multiple blocks)
            if num_id not in transistor_ids:
                param_statements.append(param_line)
                transistor_ids.append(num_id)

            # --- Create modified M-line ---
            new_m_line = f"{transistor_id} {nodes_and_model} w={w_param} l={l_param} m={m_param}"
            line = new_m_line
        
            # Keep other lines as is (resistors, capacitors, sources, etc.)
        modified_lines.append(line)
    output = []
    output.append("*params ")
    output.extend(param_statements)
    output.extend(modified_lines)
    
    return "\n".join(output)