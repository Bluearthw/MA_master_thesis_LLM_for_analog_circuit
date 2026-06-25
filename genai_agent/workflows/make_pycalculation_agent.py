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
1. Every generated function MUST accept exactly one primary positional argument: 'raw_data' (a 2D numpy array representing the simulation output).
2. Every function MUST process the arrays using numpy operations and return exactly ONE scalar comparable float/int value (for the RL sizer reward function evaluation loop).
3. Do not cross-contaminate functions. Generate a distinct, isolated function definition object for EVERY contract item provided.
4. If rawdata is None, return negative specification integer ID e.g. -31.0 for calc_spec_31. For other error return, use different decimal like -31.1 and -31.2 to differentiate.
Example naming layout style:
def calc_spec_31(raw_data):
    import numpy as np
    # calculation steps...
    return float(result)

[TASK]
Generate the complete list of standalone Python plugin functions matching the validation schema requirements."""

    try:
        struc = agent_utils.call_agent(contents=contents, response_schema=response_schema.Struct_make_pycal_func_list)
        
        return struc
    except Exception as e:
        # Re-raise so upstream code can decide how to handle persistent failures.
        print(f"calculation_rule_builder: call_agent failed: {e}")
        raise