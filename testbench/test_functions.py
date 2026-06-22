from google import genai
from google.genai import types
import os
import sys
from pydantic import BaseModel, Field
import time
import numpy as np
import pandas as pd
## local imports
import genai_agent.data.saved_netlist as saved_netlist
sys.path.append('.')
from utils import gen_utils
from genai_agent.data import local_config
from genai_agent.workflows import make_prompt_agent
def test_clean():
    for i in range(2, 20):
        cir_path = f"../material/dataset/tb_dataset/{i}/{i}.cir"
        # print(i)
        # print("cir_path",cir_path)
        if not os.path.isfile(cir_path):
            continue
        circuit_string = gen_utils.get_file_to_str(
            cir_path,
            ""
            
        )
        circuit_string = gen_utils.clean_netlist(circuit_string)
        print("==clean\n", circuit_string)
    return circuit_string

def test_add_params(netlist=""):
    netlist = """
.include "1genai/data/45nm.sp"
M0 VDD VDD VOUT1 VSS nmos
R0 VOUT1 VSS
C0 VOUT1 VSS
"""
    """

    .include "./1genai/data/45nm.sp"
    M1 VOUT2 VIN2 IB1 VSS nmos
    M0 VOUT1 VIN1 IB1 VSS nmos
    M3 VOUT2 VB1 VDD VDD nmos
    M2 VOUT1 VB1 VDD VDD nmos
    R1 VDD VOUT1
    R0 VDD VOUT2
    """
    # lines = netlist # does not work, need to split first
    # lines = netlist.strip().split('\n')# , add this line if the netlist is not identified as lines
    # print(netlist)
    nl = utils.add_params(netlist)  # input should be line here
    print("==add_para", nl)

def test_add_source(netlist=""):
    netlist = """

*params 
.param w1=0.5u l1=90n m1=1
.param w0=0.5u l0=90n m0=1
.param w3=0.5u l3=90n m3=1
.param w2=0.5u l2=90n m2=1
.param r1=1k
.param r0=1k
.include "./1genai/data/45nm.sp"
M1 VOUT2 VIN2 IB1 VSS nmos w=w1 l=l1 m=m1
M0 VOUT1 VIN1 IB1 VSS nmos w=w0 l=l0 m=m0
M3 VOUT2 VB1 VDD VDD nmos w=w3 l=l3 m=m3
M2 VOUT1 VB1 VDD VDD nmos w=w2 l=l2 m=m2
R1 VDD VOUT1 {r1}
R0 VDD VOUT2 {r0}
    """
    # lines = netlist # does not work, need to split first
    # print(netlist)
    nl = gen_utils.add_DC_source(netlist)  # input should be string here
    print("==add_DC", nl)

def test_add_C_load(netlist=""):
    netlist = """
*params
.param VB1=0.7
.param VDD=1.2
.param w0=0.5u l0=90n m0=1
.param w1=0.5u l1=90n m1=1
.include "1genai/data/45nm.sp"
M0 VOUT1 VB1 VDD VDD pmos w=w0 l=l0 m=m0
M1 VOUT1 VIN1 VSS VSS nmos w=w1 l=l1 m=m1

Vdd VDD 0 dc=VDD
vb1 VB1 0 dc=VB1
Vss VSS 0 dc=0
"""
    node = "VOUT1" # should be from the LLM
    nl = gen_utils.add_C_load(netlist, node)  # input should be string here
    print("==add_Cload", nl)

def test_add_add_OP_simulation(netlist=""):
    netlist = """
*params
.param VB1=0.7

.param Cload=10p
.param VDD=1.2
.param w0=0.5u l0=90n m0=1
.param w1=0.5u l1=90n m1=1
.include "1genai/data/45nm.sp"
M0 VOUT1 VB1 VDD VDD pmos w=w0 l=l0 m=m0
M1 VOUT1 VIN1 VSS VSS nmos w=w1 l=l1 m=m1

Vdd VDD 0 dc=VDD
vb1 VB1 0 dc=VB1
Vss VSS 0 dc=0

Cload VOUT1 VSS {Cload}
"""
    node = "VIN1" # should be from the LLM
    nl = gen_utils.add_OP_simulation(netlist, node)  # input should be string here
    print("==add_Cload", nl)

def test_pycpice_op_sim():
    netlist = local_config.netlist_14
    result = gen_utils.pyspice_op_sim(netlist, "vout1")  # input should be string here
    print("==pyspice_op_sim", result)

def test_modify_DC_bias():
    netlist ="""
*params 

.param VINCM=0.6

.param Cload=10p
.param VB1=0.9

.param VDD=1.2
.param w0=0.5u l0=90n m0=1
.param w1=0.5u l1=90n m1=1
.include "1genai/data/45nm.sp"
M0 VOUT1 VB1 VDD VDD pmos w=w0 l=l0 m=m0
M1 VOUT1 VIN1 VSS VSS nmos w=w1 l=l1 m=m1

vdd VDD 0 dc=VDD

vb1 VB1 0 dc=VB1

vss VSS 0 dc=0

Cload vout1 VSS {Cload}

Vicm vin1 VSS dc=VINCM

.control

option numdgt=4
set temp=25
op
.endc
.end"""
    netlist, new_V, old_V= gen_utils.modify_DC_bias(netlist,"VB1",False)
    print("==netlist\n",netlist)
    print("==new\n",new_V)
    print("==old\n",old_V)
    return 0

def test_find_OPAMP_num_from_file():
    path = "../material/dataset/tb_dataset"
    nums = gen_utils.find_OPAMP_num_from_file(path) #amplifier
    print("# ", len(nums))
    print("nums = ",nums)
    return nums

def test_find_OPAMPs_without_clk():
    path = "../material/dataset/tb_dataset"
    # nums = utils.find_OPAMP_num_from_file(path)
    nums = local_config.num_amplifier_with_vin_vout
    # print("==nums\n",nums)
    SISO_nums = gen_utils.find_OPAMPs_without_clk(path,nums)
    print("==SISO_nums\n",SISO_nums)
    print("==how much\n",len(SISO_nums))

def test_find_SISOs_from_OPAMPs():
    path = "../material/dataset/tb_dataset"
    # nums = utils.find_OPAMP_num_from_file(path)
    nums = local_config.num_amplifier_without_mixer_comparator_ports
    # print("==nums\n",nums)
    SISO_nums = gen_utils.find_SISOs_from_OPAMPs(path,nums)
    print("SISO_nums = ",SISO_nums)
    print("# ",len(SISO_nums))

    
def test_find_ports_from_nums(nums):
    dataset_path = "../material/dataset/tb_dataset"
    
    ports2 = gen_utils.find_ports_from_all(dataset_path,nums)  
    print("ports2\n",ports2)


def test_find_RF_from_cir_pattern():
    dataset_path = "../material/dataset/tb_dataset"
    # port = ["VOUT1"]
    nums1 = gen_utils.find_cir_num_with_pattern(dataset_path,["L0"])
    
    print("# ", len(nums1))
    print(nums1)


def test_find_all():
    dataset_path = "../material/dataset/tb_dataset"
    # port = ["VOUT1"]
    n = gen_utils.find_all(dataset_path)
    print("# ", len(n))
    print(n)


def test_find_cir_without_mos():
    dataset_path = "../material/dataset/tb_dataset"
    # port = ["VOUT1"]
    nums = gen_utils.find_cir_num_without_pattern(dataset_path,["nmos4", "pmos4", "npn"])
    print("# ", len(nums))
    print(nums)

def test_find_cir_without_vout():
    dataset_path = "../material/dataset/tb_dataset"
    # port = ["VOUT1"]
    port = ["VOUT1"]
    num_test = local_config.nums_with_transistors
    nums = gen_utils.find_cir_num_without_pattern(dataset_path,port,num_test)
    print("# ", len(nums))
    print(nums)

def test_find_num_from_class(id=None):
    """
    Find circuit numbers from class ID(s).
    
    Args:
        id (int or None): If int, find nums for that single class.
                         If None, find nums for all classes 1-40.
    """
    if id is None:
        # Find for all classes 1 to 40
        lines = []
        for class_id in range(1, 41):
            nums = gen_utils.find_num_from_class(class_id)
            lines.append(f"class_{class_id}:  {nums}")
            lines.append(f"len_{class_id}: {len(nums)}")
            # print(f"Class {class_id}: # {len(nums):3d} circuits - {nums[:10]}{'...' if len(nums) > 10 else ''}")
            content = "\n\n".join(lines)
            path_yaml = ".\\genai_agent\\memory\\"+f"class.yaml"
            file_utils.save_file_overwrite(path_yaml, content)
    else:
        # Find for single class
        nums = gen_utils.find_num_from_class(id)
        print(f"Class {id}: # {len(nums)}")
        print(nums)
def test_modify_duplicate_component():
    raw_netlist = """
M3 (net8 VB1 VDD VDD) pmos4
M2 (VOUT1 VB1 VDD VDD) pmos4
M1 (net8 VIN1 VSS VSS) nmos4
M0 (VOUT1 net8 VSS VSS) nmos4
C1 (VOUT1 VSS) capacitor
C1 (net8 VSS) capacitor
    """
    clean_netlist = gen_utils.modify_duplicate_component(raw_netlist)
    print(clean_netlist)

def test_find_cir_without_vdd():
    dataset_path = "../material/dataset/tb_dataset"
    # port = ["VOUT1"]
    port = ["VSS"]
    num_test = local_config.num_class_1 # only 621
    num_test = local_config.num_all#
    nums = gen_utils.find_cir_num_without_pattern(dataset_path,port,num_test)
    print("# ", len(nums))
    print(nums)
def test_pyspice_sim(nl = ""):
    # nl = local_config.nl_feb23_wuhu
    gen_utils.delete_all_files_skip_dir(local_config.path_output) # delete all previous output to avoid confusion
    
    gen_utils.pyspice_op_sim_simple(nl)
    # success = gen_utils.pyspice_op_sim(nl)
    # if success["success"]:
    #     print("Simulation successful!")
    # else:
    #     print("Simulation failed with message:", success["message"])
    success = gen_utils.pyspice_op_sim_final(nl)
    if success["success"]:
        print("Simulation successful!")
    else:
        print("Simulation failed with message:", success["message"])


def test_check_output_files():
    output_files = ["ac_gain.csv", "noise.csv"]
    for file in output_files:
        file_path = "./1genai/output/" + file
        if os.path.exists(file_path):
            print(f"File {file_path} exists.")
        else:
            print(f"File {file_path} does not exist.")

def test_debug_agent(cir_num=4):
    success = {"success": False, "message": "Error: no such vector onoise_spectrum"}
    if success["success"]:
        print("Simulation successful!")
    else:
       debug_agent.debug_agent_flow(local_config.nl_feb24, success["message"], cir_num=4)
def test_find_category_str(id):
    path_category = f"./1genai/data/categories/category{id}.md"
    str = gen_utils.get_file_to_str(path_category)
    print(str)
    # results['dc_gain'] = df.iloc[0, 1]
    # print(f"DC Gain: {results.dc_gain} dB")
def test_check_cat4_requirements():
    nums = local_config.num_class_4
    dataset_path = "../material/dataset/tb_dataset"
    new_nums = gen_utils.find_cir_num_with_pattern(dataset_path,["IIN1"],nums)
    print("==new_nums\n",new_nums)
def test_find_cat_from_num(num = 4):
    
    cat = gen_utils.find_cat_from_num(num)
    print("==cat\n",cat)

def test_cmfb_check_agent(netlist, cir_num=4):
    category_num = gen_utils.find_cat_from_num(cir_num) # for now we only have one category. In the future, we can have more categories and the sim agent will read the requirement of the category and decide what simulations to add.
    path_category = local_config.path_category_md + f"{category_num}.md"
    # or the cat_num is already known, so just +"4.md"
    category = gen_utils.get_file_to_str(path_category)
    client = gen_utils.get_client()
    contents = f"""You are an expert Analog IC Designer. You are given an incomplete netlist : {netlist}, a circuit number {cir_num}, a table of specifications and their IDs : {local_config.table_specs_id}, and a brief requirement about this type of circuit : {category}.
Your goal is to check whether there is CMFB loop in this circuit. If there is, say yes and explain shortly like 1 sentence. I think, if the IN,CM increases, the net017 can stop VOUT,CM to increase, right? That is also a CMFB, right?
"""
    response = client.models.generate_content(
                model=local_config.agent_model,
                contents=contents,
                
            )
    print(response.text)

def test_clean_before_CMFB(nl):
    nl2 = gen_utils.clean_before_CMFB(nl)
    print(nl2)

def test_cmfb_agent(nl):
    response = make_prompt_agent.make_prompt_spec_table_agent_flow(nl,182)
    print(response)
# region test
start_time = time.perf_counter()
# test_clean()
# test_add_params()
# test_add_source()
# test_add_C_load()
# test_add_add_OP_simulation()
# test_modify_DC_bias()
# test_find_OPAMP_num_from_file()
# test_find_OPAMPs_without_clk()
# test_find_SISOs_from_OPAMPs()
# test_find_ports_from_nums(local_config.num_SISOs)
# test_find_cir_without_out()
# test_find_RF_from_cir_pattern()
# test_find_all()
# test_find_cir_without_mos()

# test_modify_duplicate_component()
# test_find_cir_without_vdd()# test_check_output_files()
# test_measurement_spice_result("./1genai/output/ac_gain.csv")
# test_debug_agent()
# test_find_cat_from_num(186)
# test_clean_before_CMFB(saved_netlist.nl_182_diff_with_cmfb_before_cmfb_agent)

end_time = time.perf_counter()

# endregion

#region run ngspice
# test_pyspice_sim(local_config.nl_mar02_total)
# test_pycpice_op()



#end region

#region find type nums
# test_find_num_from_class(1)
# test_find_num_from_class(4)
# test_find_num_from_class(7)
# test_find_num_from_class(40)
test_find_num_from_class()  # Find all classes 1-40
# test_find_category_str(4)

# gen_utils.difference_of_nums(local_config.num_class_4, [43])
# gen_utils.difference_of_nums( local_config.num_amplifier_included_with_in_out,local_config.num_amplifier_without_mixer_comparator_ports)
# gen_utils.difference_of_nums( local_config.num_all, local_config.num_no_mos)

# region category4
# test_check_cat4_requirements()
#endregion category4

# region category7
#endregion category7

#region agent test
# test_cmfb_check_agent(saved_netlist.nl_182_diff_with_cmfb_not_for_sim, 182)
# test_cmfb_agent( saved_netlist.nl_182_before_cmfb_agent_cleaned)
#endregion

print(f"Execution time: {end_time - start_time:.6f} seconds")




