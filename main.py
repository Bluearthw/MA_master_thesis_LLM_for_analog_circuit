import os
from pathlib import Path
import sys
import yaml
#local import
from genai_agent.data import category_numbers
from genai_agent.data.local_config import path_output 
from genai_agent.data.local_config import spec_tables_path 
from genai_agent.workflows import workflow
from utils import gen_utils
# from genai_agent.workflows.type1_7_40_SISO_DISO_DIDO import root_agent_type1_7_40
# from genai_agent.workflows.type6_bandgap import root_agent_type6
# from genai_agent.workflows.type23_charge_pump import root_agent_type23
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

# ###############bandgap
# test = [6] 
# test = category_numbers.num_class_6_without_IIN1

# ###############SISO
# test = category_numbers.num_class_1_with_VDD_tested

# ################DIDO
# test = [182] #dido cmfb
# test = [69] #dido 
# test = [1005]
# test = category_numbers.num_class_40_samples

# ################DISO
# test = category_numbers.num_class_7_samples
# test = [9]
# Convert tested to a set first for blazing fast lookups
############### oscillator
test = category_numbers.num_class_2
# tested = category_numbers.num_class_40_samples_tested
# tested_set = set(tested)
# test = [item for item in test if item not in tested_set] # Keep only the items that aren't in the tested set
test = [test[0]]
# test = test[1:5]

workflow_goal = 4 # only with spec table update and prompt creation
workflow_goal = 0 # only with netlist gen
# workflow_goal = 1 # whole workflow
# workflow_goal = 2 # only with RL sizer
# workflow_goal = 3 # only with yaml creation
user_interation_utils.print_status(workflow_goal, test)
# sys.exit(0)

spec_id_unified = file_utils.get_dict_from_json(spec_tables_path)
specifications_table = spec_id_unified["specifications"]
list_min_targets = agent_utils.get_list_min_targets(specifications_table)
valid_contracts = None
if workflow_goal == 2:
    i = test[0]
    td3_runner.td3_start(circuit_name=f'{i}', list_min_targets=list_min_targets)
elif workflow_goal == 3:
    i = test[0]

    path_yaml = f'./genai_agent/output/{i}/temp.yaml'
    with open(path_yaml, 'r') as f:
            yaml_data = yaml.load(f, Loader=yaml.Loader)
    path_netlist = yaml_data['path_nl']
    i = yaml_data['cir_name']
    data_for_dut_yaml = yaml_data['data_for_dut_yaml']
    specifications_table = spec_id_unified["specifications"]
    target_id_dict = agent_utils.make_dictionary_from_specifications("target_id", specifications_table)
    spec_default_values = None #!!!
    path_yaml = yaml_creation.make_full_yaml(path_netlist, path_ids=yaml_data['path_ids'], cir_name=i, data_for_dut_yaml=data_for_dut_yaml, spec_id_dict=target_id_dict, spec_default_values=spec_default_values)
    print("yaml path = ", path_yaml)
else:
    for i in test:
        print("######*======",i)

        output_dir = Path(f"{path_output}{i}")
        output_dir.mkdir(parents=True, exist_ok=True)
        path_output_num, category_num, category_str, netlist, has_input, is_diff, cat_json = gen_utils.pre_process_circuit(i)
        print("####is_diff =", is_diff)
        # print("####cat_json =", cat_json)
        # sys.exit(0)
        general_rules, category_gen_rules, category_debug_rules, is_cat_propmt_exist, cat_prompt_path = agent_utils.prepare_workflow_prompts_json(category_num)
        print("is_cat_propmt_exist =", is_cat_propmt_exist)
        if not is_cat_propmt_exist or workflow_goal == 4:
            spec_id_unified, valid_contracts = workflow.prepare_new_type(cat_prompt_path, cat_json, spec_tables_path, spec_id_unified)
            specifications_table = spec_id_unified["specifications"]
            list_min_targets = agent_utils.get_list_min_targets( specifications_table)
            # specifications_table = spec_id_unified["specifications"]
            # spec_name_id_dict = agent_utils.make_dictionary_from_specifications("spec_name", specifications_table)
            
        aliases = agent_utils.make_dictionary_from_specifications("aliases", specifications_table)
        num_id_spec_name_dict = agent_utils.make_dictionary_from_specifications("spec_name", specifications_table)
        trimmed_spec_name_table = agent_utils.trim_spec_table(category_str, num_id_spec_name_dict, aliases)
        target_id_dict = agent_utils.make_dictionary_from_specifications("target_id", specifications_table)
        # contracts_dict = agent_utils.make_dictionary_from_specifications("contract", specifications_table)
        file_utils.save_dict_to_json(target_id_dict, f"{path_output_num}target_id_dict.json")
        if valid_contracts is None:
            required_builtin_num_id_specs, required_num_id_specs_with_contracts = agent_utils.get_required_spec_contracts(trimmed_spec_name_table, specifications_table)
            valid_contracts = required_num_id_specs_with_contracts

        print("general_rules =", general_rules)
        # print("###trimmed_spec_table",trimmed_spec_table)
        
        if workflow_goal == 4:
            sys.exit(0)
        results, struct_path_id, path_netlist, spec_sims, data_for_dut_yaml = workflow.generate_netlist(
        cir_num=i, 
        path_output_num=path_output_num, 
        netlist=netlist, 
        has_input=has_input, 
        trimmed_spec_name_table=trimmed_spec_name_table,
        is_diff= is_diff,
        category_num= category_num,
        general_rules = general_rules,
        cat_json = cat_json,
        category_gen_rules = category_gen_rules,
        category_debug_rules = category_debug_rules,
        contracts = valid_contracts,
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

        spec_default_values = agent_utils.make_dictionary_from_specifications("default_value", specifications_table)
        
        path_yaml = yaml_creation.make_full_yaml(path_netlist, path_ids=struct_path_id, cir_name=i, data_for_dut_yaml=data_for_dut_yaml, spec_id_dict=target_id_dict, spec_default_values=spec_default_values)
        print("yaml path = ", path_yaml)
        print("====yaml done=======",i)  
        if workflow_goal == 1:
            print("##list_min_targets = ",list_min_targets)
            td3_runner.td3_start(circuit_name=f'{i}', list_min_targets=list_min_targets)
        
        gen_utils.test_delay(30)

