from genai_agent.data import local_config
from genai_agent.data import response_schema
from utils import agent_utils

def debug_agent_flow(netlist, formatted_history_input, cir_num, spec_sims, general_rules):
    """Call the debug agent to fix a netlist and return the parsed response model.

    - `general_rules` is expected to be a list of rule lines (from workflow_prompts.json).
    - The function is resilient to either a simple Struct_debug (netlist/spec_sims/fix_info)
      or an extended Struct_debug that also includes `bug_analysis` and `fix_plan`.
    """
    print("==netlist in debug agent\n", netlist)
    print("==error_message\n", formatted_history_input)

    # Ensure general_rules is a string block when interpolated into the prompt.
    if isinstance(general_rules, (list, tuple)):
        general_rules_block = "\n".join(general_rules)
    else:
        general_rules_block = str(general_rules)

    contents = f"""You are an expert Analog IC Designer, Circuit Architect, and NGSpice Specialist. 
Your task is to analyze a failed SPICE simulation, review any past debugging attempts, and output a corrected, fully functional netlist.

### Inputs & Context
1. **Current Failed Netlist:**
```spice
{netlist}
2. **Simulation History & Errors:**
{formatted_history_input}

3. **Global Design Rules:**
{general_rules_block}

4. **Reference Specifications:**

Specification ID Table: {local_config.table_specs_id}

Required Simulations (from previous agent): {spec_sims}

General Rules:{general_rules_block}
"""

    # Delegate retry/backoff and error handling to a central helper.
    try:
        struc = agent_utils.call_agent(contents=contents, response_schema=response_schema.Struct_debug)

        # Robust printing for both simple and extended Struct_debug variants
        if hasattr(struc, 'bug_analysis'):
            print("==bug analysis:\n", getattr(struc, 'bug_analysis'))
        if hasattr(struc, 'fix_plan'):
            print("==fix plan:\n", getattr(struc, 'fix_plan'))

        print("==netlist after debug", getattr(struc, 'netlist', None))
        print("==debug agent spec sims", getattr(struc, 'spec_sims', None))
        print("==debug agent fix info", getattr(struc, 'fix_info', None))

        return struc
    except Exception as e:
        # Re-raise so upstream code can decide how to handle persistent failures.
        print(f"debug_agent_flow: call_agent failed: {e}")
        raise
