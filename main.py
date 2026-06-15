from pathlib import Path
import sys
import yaml
#local import
from genai_agent.data import category_numbers
from genai_agent.data.local_config import path_output 
from genai_agent.data.local_config import path_prompts 
from genai_agent.workflows import workflow
from utils import gen_utils
from genai_agent.workflows.type1_7_40_SISO_DISO_DIDO import root_agent_type1_7_40
from genai_agent.workflows.type6_bandgap import root_agent_type6
from genai_agent.workflows.type23_charge_pump import root_agent_type23
from utils import yaml_creation
from utils import agent_utils
from utils import file_utils
from utils import user_interation_utils
import td3_runner
test = category_numbers.num_class_40[:10]
test = [69, 182] # cmfb or without cmfb
test = [9, 155, 69, 182, 439, 381] # try to have siso diso dido dido_cmfb，charge pump, bandgap
# test = [9] #siso
# test = [155] #diso
# test = [69] #dido
# charge pump
test = category_numbers.num_class_23
test = [439]# charge pump class_23:  [439, 440, 549, 550, 551, 552, 553, 603]

#bandgap
# test = [6] 
# test = category_numbers.num_class_6_without_IIN1
# #SISO
# test = category_numbers.num_class_1_with_VDD_tested
# #DIDO
# test = [182] #dido cmfb
# test = [69] #dido 
test = [1005]
# test = category_numbers.num_class_40_samples
# #DISO
# test = category_numbers.num_class_7_samples
# test = [9]
# Convert tested to a set first for blazing fast lookups

# tested = category_numbers.num_class_40_samples_tested
# tested_set = set(tested)
# test = [item for item in test if item not in tested_set] # Keep only the items that aren't in the tested set


is_with_RL = 0 # only with netlist gen
# is_with_RL = 1 # whole workflow
# is_with_RL = 2 # only with RL sizer
# is_with_RL = 3 # only with yaml creation
user_interation_utils.print_status(is_with_RL, test)
# sys.exit(0)

if is_with_RL == 2:
    i = test[0]
    td3_runner.td3_start(circuit_name=f'{i}')
elif is_with_RL == 3:
    i = test[0]

    path_yaml = f'./genai_agent/output/{i}/temp.yaml'
    with open(path_yaml, 'r') as f:
            yaml_data = yaml.load(f, Loader=yaml.Loader)
    path_netlist = yaml_data['path_nl']
    i = yaml_data['cir_name']
    data_for_dut_yaml = yaml_data['data_for_dut_yaml']
    path_yaml = yaml_creation.make_full_yaml(path_netlist, path_ids=yaml_data['path_ids'], cir_name=i, data_for_dut_yaml=data_for_dut_yaml)
    print("yaml path = ", path_yaml)
else:
    for i in test:
        print("=====*======",i)

        output_dir = Path(f"{path_output}{i}")
        output_dir.mkdir(parents=True, exist_ok=True)
        path_output_num, category_num, category_str, netlist, has_input, is_diff = gen_utils.pre_process_circuit(i)
        print("is_diff =", is_diff)
        file_utils.delete_all_files_except_dir(path_output_num)
        trimmed_spec_table = gen_utils.trim_spec_table(category_str)
        print("trimmed_spec_table",trimmed_spec_table)

        dict = agent_utils.get_workflow_prompts()# should update for every circuit, in the future, some flag to control
        general_rules = "\n".join(dict.get('general_rules'))
        print("general_rules =", general_rules)
        results, struct_path_id, path_netlist, spec_sims, data_for_dut_yaml = workflow.generate_netlist(
        cir_num=i, 
        path_output_num=path_output_num, 
        category_str=category_str, 
        netlist=netlist, 
        has_input=has_input, 
        trimmed_spec_table=trimmed_spec_table,
        is_diff=is_diff,
        category_num=category_num,
        general_rules = general_rules
        )
        struct_path_id = {k: v for k, v in struct_path_id.items() if k != 16 and k != 15} # remove some array results
        print("====netlist generation done=======",i)
        
        data = {
        'cir_name': i,
        'path_nl': path_netlist,
        'path_ids': struct_path_id,
        'spec_sims': spec_sims,
        'data_for_dut_yaml': data_for_dut_yaml,
        
        }
        yaml_creation.save_temp(data) #this is for test.
        
        path_yaml = yaml_creation.make_full_yaml(path_netlist, path_ids=struct_path_id, cir_name=i, data_for_dut_yaml=data_for_dut_yaml)
        print("yaml path = ", path_yaml)
        print("====yaml done=======",i)  
        if is_with_RL == 1:
            td3_runner.td3_start(circuit_name=f'{i}')
        
        gen_utils.test_delay(30)

