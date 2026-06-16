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

def netlist_builder(netlist, category_json, category_num, cir_num=4, trimmed_spec_table=None, is_diff=False, general_rules=None, category_gen_rules=None):
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
    if not os.path.isfile(prompt_path):
        
        # Final fallback: build a minimal prompt inline, 
        ## !! or create one with agent!
        print(f"Warning: prompt for category {category_num} not found, using minimal inline prompt.")
        contents = f"You are given a netlist: {netlist}\nPlease produce a ready-to-run netlist and a list of spec simulations."
    category_json = json.dumps(category_json, indent=4)
    contents = file_utils.get_file_to_str(prompt_path).format(general_rules=general_rules,
                                                            f_end=f_end, 
                                                            line_wrdata_path_num=line_wrdata_path_num, 
                                                            netlist=netlist,
                                                            is_diff = is_diff,
                                                            trimmed_spec_table = trimmed_spec_table,
                                                            category = category_json,
                                                            cir_num = cir_num
                                                            )
    if category_gen_rules != "":
        contents = contents + "\n**More advice about this category**: " + category_gen_rules
    print("###contents netlist builder ", contents)
    try:
        struc = agent_utils.call_agent(contents=contents, response_schema=response_schema.Struct_flow)
        print("==struc_netlist_builder", struc)
        return struc
    except Exception as e:
        # Re-raise so upstream code can decide how to handle persistent failures.
        print(f"netlist_builder: call_agent failed: {e}")
        raise

    




