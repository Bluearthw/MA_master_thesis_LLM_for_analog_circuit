import sys
sys.path.append(".")
from utils import gen_utils
from genai_agent import local_config
from genai_agent.memory import category_numbers
def test_count_retry_info(cir_nums):
    total, average = gen_utils.count_retry_info(cir_nums)
    print(f"Total retries: {total}, Average retries: {average}")

def test_find_cir_num_without_pattern(nums, port = []):
    dataset_path = "../material/dataset/tb_dataset"

    nums_new = gen_utils.find_cir_num_without_pattern(dataset_path,port,nums)
    print("#old ", len(nums))
    print(nums)
    print("#new ", len(nums_new))
    print(nums_new)

test = [439, 440, 549, 550, 551, 552, 553, 603] # charge pump
# test_count_retry_info(test)

bandgap_nums = category_numbers.num_class_6
test_find_cir_num_without_pattern(bandgap_nums,["IIN1"])