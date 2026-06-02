import sys
sys.path.append(".")
from utils import gen_utils

def test_count_retry_info(cir_nums):
    total, average = gen_utils.count_retry_info(cir_nums)
    print(f"Total retries: {total}, Average retries: {average}")

test = [439, 440, 549, 550, 551, 552, 553, 603] # charge pump
test_count_retry_info(test)