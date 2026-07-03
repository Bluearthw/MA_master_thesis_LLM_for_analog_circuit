import sys
from pathlib import Path
import yaml

from genai_agent.data import category_numbers
from genai_agent.data.local_config import path_output, spec_tables_path
from genai_agent.workflows import workflow
from utils import agent_utils, file_utils, gen_utils, user_interation_utils, yaml_creation
import td3_runner

WORKFLOW_LABELS = {
    0: "netlist generation only",
    1: "full workflow",
    2: "RL sizer only",
    3: "yaml creation only",
    4: "prompt/spec update only",
}


def select_test_set():
    """Return the list of circuits to run for this session."""
    # Choose one of the examples below and keep only one active assignment.
    # return category_numbers.num_class_40[:10]
    # return [69, 182]
    # return [9, 155, 69, 182, 439, 381]
    # return category_numbers.num_class_23
    # return [439]
    # return category_numbers.num_class_2_without_IIN1
    test_num = [9] #simplest SISO
    return test_num


def get_workflow_goal():
    """Return the current workflow mode for main execution."""
    # 0: netlist generation only
    # 1: whole workflow
    # 2: RL sizer only
    # 3: yaml creation only
    # 4: spec/prompt update only
    workflow_goal = 2
    return workflow_goal


def create_output_dir(circuit_id):
    output_dir = Path(f"{path_output}{circuit_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def load_specification_data():
    spec_id_unified = file_utils.get_dict_from_json(spec_tables_path)
    specifications_table = spec_id_unified["specifications"]
    return spec_id_unified, specifications_table


def update_prompt_spec_if_needed(category_num, cat_json, spec_id_unified, workflow_goal):
    """Prepare prompt files and refresh spec contracts when needed."""
    general_rules, category_gen_rules, category_debug_rules, is_cat_prompt_exist, cat_prompt_path = agent_utils.prepare_workflow_prompts_json(category_num)

    if not is_cat_prompt_exist or workflow_goal == 4:
        spec_id_unified, valid_contracts = workflow.prepare_new_type(
            cat_prompt_path, cat_json, spec_tables_path, spec_id_unified
        )
        return spec_id_unified, valid_contracts, general_rules, category_gen_rules, category_debug_rules

    return spec_id_unified, None, general_rules, category_gen_rules, category_debug_rules


def normalize_struct_path_id(struct_path_id):
    filtered_struct_path_id = {}
    for k, v in struct_path_id.items():
        normalized_key = int(k) if isinstance(k, str) and k.isdigit() else k
        if normalized_key in (15, 16):
            continue
        filtered_struct_path_id[normalized_key] = v
    return filtered_struct_path_id


def handle_workflow_mode_3_make_yaml(test_nums, specifications_table):
    """Generate a full yaml file from the saved temporary yaml data."""
    path_yaml = f"./genai_agent/output/{test_nums[0]}/temp.yaml"
    with open(path_yaml, "r", encoding="utf-8") as f:
        yaml_data = yaml.load(f, Loader=yaml.Loader)

    path_netlist = yaml_data["path_nl"]
    cir_name = yaml_data["cir_name"]
    data_for_dut_yaml = yaml_data["data_for_dut_yaml"]

    target_id_dict = agent_utils.make_dictionary_from_specifications("target_id", specifications_table)
    spec_default_values = None
    path_yaml = yaml_creation.make_full_yaml(
        path_netlist,
        path_ids=yaml_data["path_ids"],
        cir_name=cir_name,
        data_for_dut_yaml=data_for_dut_yaml,
        spec_id_dict=target_id_dict,
        spec_default_values=spec_default_values,
    )
    print("yaml path =", path_yaml)


def run_circuit_workflow(i, workflow_goal, list_min_targets, spec_id_unified, specifications_table, valid_contracts):
    print("######*======", i)
    create_output_dir(i)

    path_output_num, category_num, category_str, netlist, has_input, is_diff, cat_json = gen_utils.pre_process_circuit(i)
    print("####is_diff =", is_diff)

    spec_id_unified, valid_contracts, general_rules, category_gen_rules, category_debug_rules = update_prompt_spec_if_needed(
        category_num, cat_json, spec_id_unified, workflow_goal
    )
    specifications_table = spec_id_unified["specifications"]
    list_min_targets = agent_utils.get_list_min_targets(specifications_table)

    aliases = agent_utils.make_dictionary_from_specifications("aliases", specifications_table)
    num_id_spec_name_dict = agent_utils.make_dictionary_from_specifications("spec_name", specifications_table)
    trimmed_spec_name_table = agent_utils.trim_spec_table(category_str, num_id_spec_name_dict, aliases)
    target_id_dict = agent_utils.make_dictionary_from_specifications("target_id", specifications_table)
    file_utils.save_dict_to_json(target_id_dict, f"{path_output_num}target_id_dict.json")

    if valid_contracts is None:
        _, valid_contracts = agent_utils.get_required_spec_contracts(trimmed_spec_name_table, specifications_table)

    print("general_rules =", general_rules)
    if workflow_goal == 4:
        sys.exit(0)

    _, struct_path_id, path_netlist, spec_sims, data_for_dut_yaml = workflow.generate_netlist(
        cir_num=i,
        path_output_num=path_output_num,
        netlist=netlist,
        has_input=has_input,
        trimmed_spec_name_table=trimmed_spec_name_table,
        is_diff=is_diff,
        category_num=category_num,
        general_rules=general_rules,
        cat_json=cat_json,
        category_gen_rules=category_gen_rules,
        category_debug_rules=category_debug_rules,
        contracts=valid_contracts,
    )

    struct_path_id = normalize_struct_path_id(struct_path_id)
    print("====netlist generation done=======", i)

    data = {
        "cir_name": i,
        "path_nl": path_netlist,
        "path_ids": struct_path_id,
        "spec_sims": spec_sims,
        "data_for_dut_yaml": data_for_dut_yaml,
    }
    yaml_creation.save_temp(data)

    spec_default_values = agent_utils.make_dictionary_from_specifications("default_value", specifications_table)
    path_yaml = yaml_creation.make_full_yaml(
        path_netlist,
        path_ids=struct_path_id,
        cir_name=i,
        data_for_dut_yaml=data_for_dut_yaml,
        spec_id_dict=target_id_dict,
        spec_default_values=spec_default_values,
    )
    print("yaml path =", path_yaml)
    print("====yaml done=======", i)

    if workflow_goal == 1:
        print("##list_min_targets =", list_min_targets)
        td3_runner.td3_start(circuit_name=f"{i}", list_min_targets=list_min_targets)

    gen_utils.test_delay(30)
    return spec_id_unified, valid_contracts, list_min_targets


def main():
    test_nums = select_test_set()
    workflow_goal = get_workflow_goal()
    user_interation_utils.print_status(workflow_goal, test_nums)
    gen_utils.test_delay(1, "init info")
    spec_id_unified, specifications_table = load_specification_data()
    list_min_targets = agent_utils.get_list_min_targets(specifications_table)
    valid_contracts = None

    if workflow_goal == 2:
        td3_runner.td3_start(circuit_name=f"{test_nums[0]}", list_min_targets=list_min_targets)
        return

    if workflow_goal == 3:
        handle_workflow_mode_3_make_yaml(test_nums, specifications_table)
        return

    for i in test_nums:
        spec_id_unified, valid_contracts, list_min_targets = run_circuit_workflow(
            i,
            workflow_goal,
            list_min_targets,
            spec_id_unified,
            specifications_table,
            valid_contracts,
        )


if __name__ == "__main__":
    main()
