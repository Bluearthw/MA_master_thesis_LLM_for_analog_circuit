import json
import sys
import os
#local import
sys.path.append(".")
from utils import file_utils
from utils import agent_utils
from genai_agent.data import local_config
from genai_agent.data import response_schema

def make_pycalculation_agent_flow(contracts, category_json):
    category_str = json.dumps(category_json, indent=4)
    contracts_str = json.dumps(contracts, indent=4)
    
    contents = f"""You are an expert Python Backend Engineer specializing in data parsing pipelines for Analog IC Design Automation.

You are given specific category circuit topology information:
{category_str}

And explicit contracts detailing the simulation data file paths, expected column layouts, and mathematical intent:
{contracts_str}

[CRITICAL RULES]
1. Every generated function MUST accept exactly one primary positional argument: 'data_paths' (a List[str] containing the absolute paths to the simulation output CSV files).
2. If the contract specifies a single file, access it via 'data_paths[0]'. If it specifies multiple files (e.g., multi-point sweeps like low/mid/high boundaries), parse each file via its corresponding index.
3. Every function MUST load its file data natively inside the function block using numpy (e.g., `raw_data = np.genfromtxt(data_paths[0], autostrip=True, skip_header=1)`).
4. Every function MUST process the parsed data vectors and return exactly ONE scalar comparable float/int value (for the RL sizer reward function evaluation loop).
5. Do not cross-contaminate functions. Generate a distinct, isolated function definition object for EVERY contract item provided.
6. Error Handling Strategy:
   - If 'data_paths' is None or empty, return the negative specification integer ID as a float (e.g., -32.0 for calc_spec_32).
   - If a file is missing on disk or parsing fails, return an explicit fractional identifier (e.g., -32.1 for file-not-found, -32.2 for mathematical calculation errors) to differentiate failures in the RL tracking log.

Example naming and implementation layout style:

# Example A: Single file specification (e.g., Center Frequency)
def calc_spec_31(data_paths):
    import numpy as np
    import os
    if not data_paths or not os.path.exists(data_paths[0]):
        return -31.1
    try:
        raw_data = np.genfromtxt(data_paths[0], autostrip=True, skip_header=1)
        # calculation steps using raw_data...
        return float(result)
    except Exception:
        return -31.2

# Example B: Multi-file specification (e.g., Tuning Range & Gain)
def calc_spec_32(data_paths):
    import numpy as np
    import os
    if len(data_paths) < 2:
        return -32.0
    try:
        # Load and process multiple files sequentially from the input list
        data_low = np.genfromtxt(data_paths[0], autostrip=True, skip_header=1)
        data_high = np.genfromtxt(data_paths[1], autostrip=True, skip_header=1)
        # Calculate cross-file metrics (e.g., delta_freq / delta_vctrl)
        return float(calculated_gain)
    except Exception:
        return -32.2

[TASK]
Generate the complete list of standalone Python plugin functions matching the validation schema requirements."""

    try:
        struc = agent_utils.call_agent(contents=contents, response_schema=response_schema.Struct_make_pycal_func_list)
        
        return struc
    except Exception as e:
        # Re-raise so upstream code can decide how to handle persistent failures.
        print(f"calculation_rule_builder: call_agent failed: {e}")
        raise