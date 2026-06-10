import os
import sys
sys.path.append(".")
from utils import gen_utils
from genai_agent import local_config
from genai_agent.data import category_numbers
def test_count_retry_info(cir_nums):
    total, average, zero_retry_count = gen_utils.count_retry_info(cir_nums)
    print(f"Total retries: {total}, Average retries: {average}, Zero retries: {zero_retry_count}")

def test_find_cir_num_without_pattern(nums, port = []):
    dataset_path = "../material/dataset/tb_dataset"

    nums_new = gen_utils.find_cir_num_without_pattern(dataset_path,port,nums)
    print("#old ", len(nums))
    print(nums)
    print("#new ", len(nums_new))
    print(nums_new)

def test_trim_spec_table(category_num):
    print(local_config.path_category)
    path_category = local_config.path_category + f"{category_num}.md"
    print(path_category)
    # or the cat_num is already known, so just +"4.md"
    category_str = gen_utils.get_file_to_str(path_category)
    new_dict = gen_utils.trim_spec_table(category_str)
    print("old_dict:\n", local_config.table_specs_id)
    print("new_dict:\n", new_dict)

def test_save_load_prompt():
    
    os.makedirs(local_config.path_prompts , exist_ok=True)
    prompt_path = os.path.join(local_config.path_prompts , f"prompt_test.md")

    f_end = "1T"
    general_rules = local_config.general_rules.replace('{f_end}', f_end)
    contents = """You are a......
0. Gain example, the VOUT1 is the output node. Example:* for gain
ac dec 10 1 {f_end}
Vinput aid VSS dc=0.0 ac=1.0 PULSE({{-VHIGH*0.5}}
{general_rules} 
"""
    gen_utils.save_str_to_file(contents, prompt_path)
    return prompt_path
def test_get_prompt():
    f_end = "1T"
    prompt_dir = local_config.path_prompts 
    prompt_path = os.path.join(prompt_dir, f"prompt_test.md")
    general_rules = local_config.general_rules.replace('{f_end}', f_end)
    # result = gen_utils.get_file_to_str(prompt_path).replace('{general_rules}', general_rules).replace('{f_end}', f_end)
    # result = gen_utils.get_file_to_str(prompt_path).format(general_rules=general_rules, f_end=f_end)
    result = gen_utils.get_file_to_str(prompt_path).format(general_rules=general_rules,
                                                           f_end=f_end, 
                                                           line_wrdata_path_num="line_wrdata_path_num", 
                                                           netlist="netlist",
                                                           is_diff = "is_diff",
                                                           trimmed_spec_table = "trimmed_spec_table",
                                                           category = "category",
                                                           cir_num = "cir_num"
                                                           )
    print(result)

charge_pump_nums = [439, 440, 549, 550, 551, 552, 553, 603] # charge pump\
bandgap_nums = category_numbers.num_class_6_without_IIN1
amplifier_nums = category_numbers.num_class_40_samples_tested
# test_count_retry_info(bandgap_nums)

bandgap_nums_old = category_numbers.num_class_6
# test_find_cir_num_without_pattern(bandgap_nums_old,["IIN1"])


# test_trim_spec_table(1)
# test_save_load_prompt()
test_get_prompt()