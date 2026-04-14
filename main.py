from pathlib import Path
import sys

#local import
from genai_agent.memory import category_numbers
from genai_agent.local_config import path_output 
from utils.gen_utils import test_delay
from genai_agent.workflows.type40 import root_agent_type40
from utils import yaml_creation
import td3_runner
test = category_numbers.num_class_40[:10]
test = [69, 182] # cmfb or without cmfb
test = [9, 155, 69, 182] # try to have siso diso dido dido_cmfb
test = [9]

is_with_RL = 0 # only with netlist gen
# is_with_RL = 1 # whole workflow
# is_with_RL = 2 # only with RL sizer
if is_with_RL == 2:
    i = test[0]
    td3_runner.td3_start(circuit_name=f'{i}')
else:
    for i in test:
        print("=====*======",i)
        print("====*=======",i)

        output_dir = Path(f"{path_output}{i}")
        output_dir.mkdir(parents=True, exist_ok=True)

        combined_results, struct_path_id, path_netlist = root_agent_type40.test_make_cir_sim(i)
        struct_path_id = {k: v for k, v in struct_path_id.items() if k != 16 and k != 2 and k != 15} # remove some array results
        print("====netlist generation done=======",i)
        path_yaml = yaml_creation.make_full_yaml(path_netlist, path_ids=struct_path_id, cir_name=i)
        print("yaml path = ", path_yaml)
        print("====yaml done=======",i)
        if is_with_RL == 1:
            td3_runner.td3_start(circuit_name=f'{i}')
        test_delay(30)