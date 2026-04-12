from pathlib import Path
import sys

#local import
from genai_agent.memory import category_numbers
from genai_agent.local_config import path_output 
from genai_agent.utils import test_delay
from genai_agent.workflows.type40 import root_agent_type40

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

        root_agent_type40.test_make_cir_sim(i)
        print("====done=======",i)
        if is_with_RL == 1:
            td3_runner.td3_start(circuit_name=f'{i}')
        test_delay(30)