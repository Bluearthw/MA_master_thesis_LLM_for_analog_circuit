import sys
sys.path.append(".")
from utils import gen_utils
from genai_agent import local_config
from genai_agent.memory import category_numbers
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
    path_category = local_config.path_category + f"{category_num}.md"
    # or the cat_num is already known, so just +"4.md"
    category_str = gen_utils.get_file_to_str(path_category)
    new_dict = gen_utils.trim_spec_table(category_str)
    print("old_dict:\n", local_config.table_specs_id)
    print("new_dict:\n", new_dict)

charge_pump_nums = [439, 440, 549, 550, 551, 552, 553, 603] # charge pump\
bandgap_nums = category_numbers.num_class_6_without_IIN1
# test_count_retry_info(bandgap_nums)

bandgap_nums_old = category_numbers.num_class_6
# test_find_cir_num_without_pattern(bandgap_nums_old,["IIN1"])


test_trim_spec_table(1)