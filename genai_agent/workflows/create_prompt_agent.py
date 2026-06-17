from google import genai
import sys

#local import
sys.path.append(".")
from utils import gen_utils
from utils import agent_utils
from genai_agent.data import local_config
from genai_agent.data import response_schema

def create_prompt_flow(category_json):
    contents = f"Given the simple category description: {category_json}\n" + """# Role & Purpose
You are an AI Prompt Engineer and Senior Analog IC Verification Architect. Your job is to take a raw analog circuit category description and compile a precise, production-grade System Prompt for a downstream NGSpice Netlist Generation Agent.

# Task Instructions
1. **Analyze Input**: Read the provided category information.
2. **Synthesize Simulation Block**: For every item in `required_specs`, use your expert knowledge of electrical engineering to draft an explicit NGSpice test execution case. You must specify:
   - The type of simulation analysis needed (`.ac`, `.dc`, `.tran`, `.op`).
   - The concrete `.control` block formatting syntax using `{line_wrdata_path_num}` for the output file naming convention. `{fend}` is also used for AC. Example: `5. **Power Supply Rejection Ratio (PSRR)**: AC analysis on supply ......\\n   - Superimpose small AC signal on VDD: Vdd VDD 0 dc=1.2 ac=0.01\\n   - Simulation: ac dec 10 1 {f_end}\\n   - Output: {line_wrdata_path_num}/ac_psrr.csv v(VOUT1)`
3. **Formulate Topology Rules**: Translate the `raw_category_prose` into structural design guidelines (e.g., how ports should be handled, whether it typically uses Differential Outputs or Common-Mode Feedback (CMFB)).
4. **Enforce Variables**: Ensure the final prompt text naturally contains the placeholders needed by the runtime runner: `{netlist}`, `{cir_num}`, `{trimmed_spec_table}`, `{category_str}`, `{line_wrdata_path_num}`, and `{general_rules}`. Example:`You are an expert Analog IC Designer and NGSpice Specialist. You are given an incomplete netlist : {netlist}, a circuit number {cir_num}, a table of specifications and their IDs to look up : {trimmed_spec_table}, and a brief requirement about this type of circuit : {category_str}. \\n\\nAlso, previous about differential output check is given: {is_diff}. If it is True: 1, the netlist is very likely to be differential output. 2, do not use DC gain but DM gain for measurement!\\n\\nYour goal is to ......`
5. **Last Line**: The last line should be {general_rules}. Example:`### General Netlist Rules:\\n 0. **Circuit requirements**: ...... 1. **Differential check**: ...... 2. **CMFB stability**: ...... {general_rules} `

# Output Format
Your response must be a clean, unquoted text block containing the finalized markdown system prompt, which will be used by next agent to generate netlists to do simulations."""
    try:
        struc = agent_utils.call_agent(contents=contents, response_schema=response_schema.Struct_create_prompt)
        print("==struc_netlist_builder", struc)
        return struc
    except Exception as e:
        # Re-raise so upstream code can decide how to handle persistent failures.
        print(f"netlist_builder: call_agent failed: {e}")
        raise