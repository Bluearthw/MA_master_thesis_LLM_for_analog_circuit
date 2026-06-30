import sys
sys.path.append('.')
from genai_agent.data import category_numbers
from utils import gen_utils
from genai_agent.data.local_config import path_dataset
from genai_agent.data.local_config import path_cir

def test_find_ports_from_cir_nums(nums):
    
    ports2 = gen_utils.find_ports_from_cir_nums(path_dataset,nums)  
    print("ports2 = ",ports2.sort())

def find_osc_fron_type2_cir_num():
    nums_type2 = category_numbers.num_class_2
    # gen_utils.is_port_exist(['IIN1','VIN1'])
    nums = []
    for i in nums_type2:
        path = path_cir.format(cir_num=i)
        # print(path)
        if gen_utils.is_port_exist(path, ['IIN1' ]):# Vin1 is with VCO??
            pass
        else:
            nums.append(i)
    print("Filtered_nums_without_IIN1 =", nums)
    print("Count:", len(nums))

def find_num_with_ports(nums, ports):
    filtered_nums = []
    for i in nums:
        path = path_cir.format(cir_num=i)
        if gen_utils.is_port_exist(path, ports):
            filtered_nums.append(i)
    print(f"Filtered nums with ports {ports} =", filtered_nums)
    print("Count:", len(filtered_nums))
nums = category_numbers.num_class_2
type_2_ports =  ['VDD', 'VSS', 'IIN1', 'VOUT1', 'IB1', 'IB2', 'IB3', 'VB1', 'VCONT1', 'VIN1', 'IB4', 'VOUT2', 'VB2', 'VB3', 'VB4', 'VB5', 'VCLK1', 'VCLK2', 'VCLK3', 'VCLK4', 'VOUT3', 'VOUT4', 'VCONT2']
# test_find_ports_from_cir_nums(nums)
# so no IIN1
# find_osc_fron_type2_cir_num()
find_num_with_ports(nums, ['VCONT1'])