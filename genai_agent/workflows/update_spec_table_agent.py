from google import genai
import json
import os
# import sys

######################
# local import
from genai_agent.data import local_config
from genai_agent.data import response_schema
from utils import gen_utils as gen_utils
from utils import agent_utils
from utils import file_utils

def update_table_agent_flow(missing_specs):
    """
    Args:
        missing_specs: List of string names found by the previous agent.
        current_tables_summary: A text summary showing what names already exist so it avoids duplicates.
    """
    
    contents = f"""You are a Data Engineering Agent for an Electronic Design Automation (EDA) pipeline. Your job is to take a list of newly requested circuit specifications and structure them into data blocks compatible with our database schemas.

# Missing Specifications to Process
{missing_specs}


# Schema Architectural Rules
For every missing specification provided, you must break it down into a structured object matching these system examples:

1. **table_target_id Mapping**: Create a clean, snake_case string identifier (e.g., 'dc_gain', 'slew_rate').
2. **spec_name**: Provide a clean, title-cased human-readable label. missing specs can be directly used. (e.g., 'DC Gain', 'Slew Rate').
3. **table_specs_aliases Mapping**: Provide an array of common alternative names in lowercase text (e.g., ["voltage gain", "a_v", "gain"]).
4. **table_targets_default_values Mapping**: Provide a reasonable engineering baseline float value (e.g., 10.0 for gain, 1e-6 for settling time).
5. **list_targets_to_min Mapping**: Determine if the metric is something an optimizer tries to minimize. Mark as True for things like noise, distortion, and settling time. Mark as False for gain, bandwidth, and phase margin.

# Output Format
You must output your response using the designated JSON schema. Do not assign integer IDs; the Python backend handles numerical keys automatically.
"""
    print("###contents create_tabler ", contents)
    try:
        struc = agent_utils.call_agent(contents=contents, response_schema=response_schema.Struct_Update_Tables)
        print("###struc_update_table = ", struc)

        return struc
    

    except Exception as e:
        # Re-raise so upstream code can decide how to handle persistent failures.
        print(f"update table agent: call_agent failed: {e}")
        raise






