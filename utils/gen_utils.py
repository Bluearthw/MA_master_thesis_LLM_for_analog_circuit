import re
from genai_agent.data import local_config
from utils import file_utils
from utils.netlist_utils import *
from utils.data_utils import *
from utils.debug_utils import *


def pre_process_circuit(cir_num):
    category_num = find_cat_from_num(cir_num)
    path_category = local_config.path_category_md + f"{category_num}.md"
    category_str = file_utils.get_file_to_str(path_category)

    path_output_num = local_config.path_output + f"{cir_num}/"
    cir_path = local_config.path_dataset + f"{cir_num}/{cir_num}.cir"
    circuit_string = file_utils.get_file_to_str(cir_path)

    has_input = has_port_from_nl(circuit_string)
    is_diff = has_port_from_nl(circuit_string, target_ports=["VOUT2"])

    circuit_string = modify_duplicate_component(circuit_string)
    circuit_string = clean_netlist(circuit_string)
    circuit_string = add_params(circuit_string)
    circuit_string = add_DC_source(circuit_string)

    cat_json = file_utils.get_dict_from_json(local_config.path_category_jsons + f"{category_num}.json")
    netlist = add_control(circuit_string)
    file_utils.delete_all_files_except_dir(path_output_num)
    print("==cir_str", netlist)

    return path_output_num, category_num, category_str, netlist, has_input, is_diff, cat_json
