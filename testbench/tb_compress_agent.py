import sys
sys.path.append('.')
from genai_agent.data.response_schema import Struct_specs_sim 
from utils import agent_utils
from utils import file_utils
from utils import gen_utils
from genai_agent.workflows import compress_err_info_agent
from genai_agent.data import local_config
from genai_agent.workflows import compress_err_info_agent

# debug_metadata.json

cir_num = 860
category_num = gen_utils.find_cat_from_num(cir_num) 
path_output_num = local_config.path_output + f"{cir_num}/"
path_metadata = path_output_num + "debug_metadata.json"
debug_json = file_utils.get_dict_from_json(path_metadata)
prompt_dict = agent_utils.get_workflow_prompts_json()# should update for every circuit, in the future, some flag to control
general_rules = "\n".join(prompt_dict.get('general_rules'))
print("##debug_json =",debug_json)

debug_history = debug_json['debug_history'] # use this since it is an object
compress_err_info_agent.compress_agent_flow(debug_history, general_rules, category_num)