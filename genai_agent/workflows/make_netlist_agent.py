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
#netlist builder
def make_netlist_agent_flow(netlist, category_json, category_num, cir_num=4, trimmed_spec_name_table=None, is_diff=False, general_rules=None, category_gen_rules=None, contracts=None, has_input = None, metrics_run_id=None, metrics_mode=None):
    line_wrdata_path_num = "wrdata " + local_config.path_output + str(cir_num)
    
    f_end= "1T"
    if general_rules is None:
        raise ValueError("general_rules cannot be None")
    # Prefer category-specific prompt; fallback to default prompt if missing
    if category_num == 7 or category_num == 40:
        c_num = 1
    else:
        c_num = category_num
    prompt_path = os.path.join(local_config.path_prompts, f"prompt_{c_num}.md")
    category_json = json.dumps(category_json, indent=4)
    if os.path.isfile(prompt_path):
        prompt_text = file_utils.get_file_to_str(prompt_path)
        if prompt_text is False:
            print(f"Warning: prompt for category {category_num} could not be read, using minimal inline prompt.")
            contents = f"You are given a netlist: {netlist}\nPlease produce a ready-to-run netlist and a list of spec simulations."
        else:
            contents = prompt_text.format(general_rules=general_rules,
                                          f_end=f_end,
                                          line_wrdata_path_num=line_wrdata_path_num,
                                          netlist=netlist,
                                          is_diff=is_diff,
                                          trimmed_spec_table=trimmed_spec_name_table,
                                          category_str=category_json,
                                          cir_num=cir_num)
    else:
        print(f"Warning: prompt for category {category_num} not found, using minimal inline prompt.")
        contents = f"You are given a netlist: {netlist}\nPlease produce a ready-to-run netlist and a list of spec simulations."
    contents = make_prompt(has_input, contracts, contents, category_gen_rules)
        
    
    try:
        struc = agent_utils.call_agent(
            contents=contents,
            response_schema=response_schema.Struct_flow,
            metrics_run_id=metrics_run_id,
            metrics_agent_name="netlist_gen",
            metrics_circuit_name=str(cir_num),
            metrics_mode=metrics_mode,
        )
        print("==struc_netlist_builder", struc)
        return struc
    except Exception as e:
        # Re-raise so upstream code can decide how to handle persistent failures.
        print(f"netlist_builder: call_agent failed: {e}")
        raise

def make_prompt(has_input, contracts, contents, category_gen_rules):
    # Ensure has_input has a clean string representation for the LLM
    if has_input is True:
        input_status_str = (
            "### [CIRCUIT INPUT CONFIGURATION]\n"
            "This circuit requires an active input stimulus source (e.g., vin, vdm, or pulse generators). "
            "Ensure the .control block excites these inputs appropriately. When the preprocessed netlist "
            "defines VIN_BIAS, VCM_BIAS, or IIN_BIAS, preserve those parameters and use their "
            "symbolic names consistently in source definitions, alter commands, and pulse expressions; "
            "do not replace them with numeric DC literals. For differential inputs, use VCM_BIAS as the "
            "input common-mode level and keep the differential stimulus at zero DC bias.\n"
        )
    elif has_input is False:
        input_status_str = "### [CIRCUIT INPUT CONFIGURATION]\nThis circuit is a self-biasing/autonomous block (NO active input signal source). Do NOT attempt to sweep or pulse an external input source; rely purely on VDD/VSS.\n"
    else:
        input_status_str = ""

    if contracts:
        contracts_str = json.dumps(contracts, indent=4)
        contracts_str2 = "### [SIMULATION CONTRACTS REFERENCE]\n" 
        
        # Fixed the string concatenation bug here from your original snippet:
        contracts_prompt = contracts_str2 + "The following dictionary are specification contracts for reference if thery are required." + contracts_str + "\n"
        
        # Combine everything cleanly into the final contents block
        contents = input_status_str + contracts_prompt + contents
    else:
        # If no contracts exist, still pass the input status structural rule
        contents = input_status_str + contents

    if category_gen_rules != "":
        contents = contents + "\n**More advice about this category**: " + category_gen_rules
    print("###contents netlist builder ", contents)
    return contents




