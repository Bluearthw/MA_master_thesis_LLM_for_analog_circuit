from pathlib import Path
import sys
import yaml
#local import
from genai_agent.memory import category_numbers
from genai_agent.local_config import path_output 
from utils import gen_utils
from genai_agent.workflows.type40_DIDO import root_agent_type40
from genai_agent.workflows.type6_bandgap import root_agent_type6
from genai_agent.workflows.type23_charge_pump import root_agent_type23
from utils import yaml_creation
import td3_runner
test = category_numbers.num_class_40[:10]
test = [69, 182] # cmfb or without cmfb
test = [9, 155, 69, 182] # try to have siso diso dido dido_cmfb
# test = [9] #siso
# test = [155] #diso
# test = [69] #dido
# test = [182] #dido cmfb
test = [6] #bandgap
test = [439, 440, 549, 550, 551, 552, 553, 603] # charge pump
test = [439]# charge pump class_23:  [439, 440, 549, 550, 551, 552, 553, 603]

is_with_RL = 0 # only with netlist gen
is_with_RL = 1 # whole workflow
# is_with_RL = 2 # only with RL sizer
# is_with_RL = 3 # only with yaml

if is_with_RL == 2:
    i = test[0]
    td3_runner.td3_start(circuit_name=f'{i}')
elif is_with_RL == 3:
    i = test[0]

    path_yaml = './genai_agent/output/temp.yaml'
    with open(path_yaml, 'r') as f:
            yaml_data = yaml.load(f, Loader=yaml.Loader)
    path_netlist = yaml_data['path_nl']
    i = yaml_data['cir_name']
    path_yaml = yaml_creation.make_full_yaml(path_netlist, path_ids=yaml_data['path_ids'], cir_name=i)
    print("yaml path = ", path_yaml)
else:
    for i in test:
        print("=====*======",i)
        print("====*=======",i)

        output_dir = Path(f"{path_output}{i}")
        output_dir.mkdir(parents=True, exist_ok=True)
        path_output_num, category_num, category_str, netlist, has_input = gen_utils.pre_process_circuit(i)
        if category_num == 6:
            combined_results, struct_path_id, path_netlist, spec_sims, data_for_dut_yaml = root_agent_type6.test_make_cir_sim(i, path_output_num, category_str, netlist, has_input)
        if category_num == 23:
            combined_results, struct_path_id, path_netlist, spec_sims, data_for_dut_yaml = root_agent_type23.test_make_cir_sim(i, path_output_num, category_str, netlist, has_input)
             
        else:
            # print(f"found,cat:{category_num}")
            # continue
            combined_results, struct_path_id, path_netlist, spec_sims, data_for_dut_yaml = root_agent_type40.test_make_cir_sim(i, path_output_num, category_str, netlist, has_input)
        struct_path_id = {k: v for k, v in struct_path_id.items() if k != 16 and k != 2 and k != 15 and k != 14} # remove some array results
        print("====netlist generation done=======",i)
        
        data = {
        'cir_name': i,
        'path_nl': path_netlist,
        'path_ids': struct_path_id,
        'spec_sims': spec_sims,
        'is_differential': data_for_dut_yaml[0],
        'has_input': data_for_dut_yaml[1],
        'target_dc_vout': data_for_dut_yaml[2]
        }
        yaml_creation.save_temp(data) #this is for test.
        
        path_yaml = yaml_creation.make_full_yaml(path_netlist, path_ids=struct_path_id, cir_name=i, data_for_dut_yaml=data_for_dut_yaml)
        print("yaml path = ", path_yaml)
        print("====yaml done=======",i)  
        if is_with_RL == 1:
            td3_runner.td3_start(circuit_name=f'{i}')
        # test_delay(30)