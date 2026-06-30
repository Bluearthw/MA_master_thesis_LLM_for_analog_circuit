import json
import os
import re
from genai_agent.data import local_config
from utils import file_utils


def find_all(dataset_path):
    i = 4
    exist_nums = []
    while True:
        path_nl = dataset_path + f"/{i}/{i}.cir"
        if os.path.isfile(path_nl):
            exist_nums.append(i)
        i += 1
        if i > 1044:
            break
    return exist_nums


def find_OPAMP_num_from_file(dataset_path):
    i = 4
    exist_nums = []
    while True:
        path_nl = dataset_path + f"/{i}/{i}.cir"
        if os.path.isfile(path_nl):
            ports_name_to_check = ["VIN1", "VOUT1"]
            if are_ports_all_exist(path_nl, ports_name_to_check):
                path = dataset_path + f"/{i}/edited_explanation.md"
                lines = file_utils.get_file_to_lines(path, 7)
                for line in lines:
                    if "amplifier" in line or "Amplifier" in line:
                        exist_nums.append(i)
                        break
        i += 1
        if i > 1044:
            break
    return exist_nums


def find_OPAMPs_without_clk(dataset_path, nums):
    exist_nums = []
    for i in nums:
        path_nl = dataset_path + f"/{i}/{i}.cir"
        if os.path.isfile(path_nl):
            ports_name_to_check = local_config.mixer_comparator_ports
            if not is_port_exist(path_nl, ports_name_to_check):
                exist_nums.append(i)
    return exist_nums


def find_SISOs_from_OPAMPs(dataset_path, nums):
    exist_nums = []
    for i in nums:
        path_nl = dataset_path + f"/{i}/{i}.cir"
        if os.path.isfile(path_nl):
            ports_name_to_check = local_config.differential_ports
            if not is_port_exist(path_nl, ports_name_to_check):
                exist_nums.append(i)
    return exist_nums


def difference_of_nums(nums_big, nums2):
    difference = list(set(nums_big).difference(set(nums2)))
    print("# ", len(difference))
    print(sorted(difference))


def find_cir_num_without_pattern(dataset_path, name_to_check, nums=None):
    if nums is None:
        nums = local_config.num_all
    exist_nums = []
    for i in nums:
        path_nl = dataset_path + f"/{i}/{i}.cir"
        if os.path.isfile(path_nl) and not is_port_exist(path_nl, name_to_check):
            exist_nums.append(i)
    return exist_nums


def find_cir_num_with_pattern(dataset_path, name_to_check, nums=None):
    if nums is None:
        nums = local_config.num_all
    exist_nums = []
    for i in nums:
        path_nl = dataset_path + f"/{i}/{i}.cir"
        if os.path.isfile(path_nl) and is_port_exist(path_nl, name_to_check):
            exist_nums.append(i)
    return exist_nums


def find_RF_from_cir_str(path_explain, cir_string):
    if "L0" in cir_string:
        return True
    lines = file_utils.get_file_to_lines(path_explain, 10, True)
    for line in lines:
        if "RF" in line:
            return True
    lines2 = file_utils.get_file_to_lines(path_explain, 8)
    return "RF" in "".join(lines2)


def find_ports_from_cir_nums(dataset_path, nums=None):
    if nums is None:
        nums = list(range(4, 1045))
    exist_ports = []
    for i in nums:
        path = dataset_path + f"/{i}/Port{i}.txt"
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as file:
                    cir_string = file.read()
                    cir_string = re.sub('\n', "", cir_string)
                    ports = cir_string.split(" ")
                    for port in ports:
                        if port and port not in exist_ports:
                            exist_ports.append(port)
            except FileNotFoundError:
                pass
    return exist_ports


def find_num_from_class(class_id):
    exist_nums = []
    for i in local_config.num_all:
        path = local_config.path_classified_dataset + f"/{i}/detected_class.txt"
        if int(file_utils.get_file_to_str(path)) == class_id:
            exist_nums.append(i)
    return exist_nums


def find_cat_from_num(num):
    path = local_config.path_classified_dataset + f"/{num}/detected_class.txt"
    return int(file_utils.get_file_to_str(path))


def is_port_exist(path, target_ports=["VIN1"]):
    content = file_utils.get_file_to_str(path)
    return has_port_from_nl(content, target_ports)


def are_ports_all_exist(path, target_ports=["VIN1"]):
    if os.path.isfile(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        for target_port in target_ports:
            if not re.search(rf"\b{target_port}\b", content):
                return False
        return True
    return False


def has_port_from_nl(netlist, target_ports=["VIN1", "IIN1"]):
    for target_port in target_ports:
        if re.search(rf"\b{target_port}\b", netlist):
            return True
    return False


def is_cir_debugged(cir_num):
    path = local_config.path_output + f"{cir_num}/debug_metadata.json"
    try:
        if not os.path.isfile(path):
            return False
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        retry = data.get('retry_count')
        if retry is None:
            return False
        try:
            return int(retry) != 0
        except Exception:
            return bool(retry)
    except Exception as e:
        print(f"is_cir_debugged: could not read '{path}': {e}")
        return False
