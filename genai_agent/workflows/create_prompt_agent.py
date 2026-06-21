import json
from google import genai
import sys

#local import
sys.path.append(".")
from utils import gen_utils
from utils import agent_utils
from genai_agent.data import local_config
from genai_agent.data import response_schema

def create_prompt_spec_table_agent_flow(category_json, spec_id_table):
    category_json = json.dumps(category_json, indent=4)
    spec_id_table = json.dumps(spec_id_table, indent=4)
    contents = f"""You are an AI Prompt Engineer and Senior Analog IC Verification Architect. Your job is to analyze a raw analog circuit category description, identify missing specifications, and compile a precise System Prompt for a downstream NGSpice Netlist Generation Agent.

# Input Data
- Target Category Requirements:
{category_json}

- Current System Specification Reference Table:
{spec_id_table}

# Task Instructions
1. **Analyze Input**: Read the target category requirements and cross-reference them with the system specification table.
2. **Identify Missing Specs**: If the requirements demand an electrical measurement not found in the reference table, flag it. If the spec is physically impossible to capture in a SPICE netlist environment (e.g., IC cost, physical layout area), flag it as impossible.
3. **Synthesize Simulation Blocks**: For every valid required specification, draft an explicit NGSpice test execution instruction block. Every case must specify:
   - The exact simulation analysis type (.ac, .dc, .tran, .op).
   - A strict constraint to ONLY export raw data vectors using 'wrdata' to the destination folder format: '{{line_wrdata_path_num}}/<filename>.csv'.
   - Absolutely forbid the downstream agent from using SPICE '.meas' or '.measure' commands.
4. **Enforce Global Variables**: The generated prompt must strictly treat the following tokens as template literals. Do not replace them with values: '{{netlist}}', '{{cir_num}}', '{{trimmed_spec_table}}', '{{category_str}}', '{{line_wrdata_path_num}}', '{{f_end}}', '{{is_diff}}', and '{{general_rules}}'.
5. **Prompt Termination**: The final line of the generated netlist agent prompt must end explicitly with the token '{{general_rules}}'.
6. **Power Consolidations**: Do NOT create new or separate specification IDs for dynamic power, clock power, or active power. Always map any power measurement requirements back to the existing unified `current` ID. The Python backend will automatically determine whether to process it as an operating point (.op) or a transient (.tran) current integration based on the circuit type.

# Output Requirement
Return your analysis completely mapped to the designated structural schema, ensuring the 'prompt' field contains the full markdown text block."""    
    
    try:
        struc = agent_utils.call_agent(contents=contents, response_schema=response_schema.Struct_prepare_new_type)
        print("##struc create prompt= ", struc)
        return struc
    except Exception as e:
        # Re-raise so upstream code can decide how to handle persistent failures.
        print(f"netlist_builder: call_agent failed: {e}")
        raise