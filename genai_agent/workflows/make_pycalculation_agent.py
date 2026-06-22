import json
import sys

#local import
sys.path.append(".")
from utils import gen_utils
from utils import agent_utils
from genai_agent.data import local_config
from genai_agent.data import response_schema

def make_calculation_rule_agent_flow(contracts, category_json):
    category_json = json.dumps(category_json, indent=4)
    spec_id_table = json.dumps(spec_id_table, indent=4)
    contents = f"""You are an expert Python Backend Engineer specializing in data parsing pipelines for Analog IC Design Automation.

You are given simple category infomation:{category_json} and contracts about data formatting rules between blocks:{contracts}.

[RULE]
All the function should return 1 comparable value since it will be used by RL sizer to compare.
[TASK]
generate a python functions based on the rules for following specification calculation, """
    try:
        struc = agent_utils.call_agent(contents=contents, response_schema=response_schema.Struct_make_pycal_func)
        print("##make_calculation_rule_struct= ", struc)
        return struc
    except Exception as e:
        # Re-raise so upstream code can decide how to handle persistent failures.
        print(f"calculation_rule_builder: call_agent failed: {e}")
        raise