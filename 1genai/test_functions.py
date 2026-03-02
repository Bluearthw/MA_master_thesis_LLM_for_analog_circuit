from google import genai
from google.genai import types
import os
import utils
from pydantic import BaseModel, Field
import local_config
import time
import numpy as np
import pandas as pd
def test_clean():
    for i in range(2, 20):
        cir_path = f"../material/dataset/tb_dataset/{i}/{i}.cir"
        # print(i)
        # print("cir_path",cir_path)
        if not os.path.isfile(cir_path):
            continue
        circuit_string = utils.get_file_to_str(
            cir_path,
            ""
            
        )
        circuit_string = utils.clean_netlist(circuit_string)
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
    nl = utils.add_DC_source(netlist)  # input should be string here
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
    nl = utils.add_C_load(netlist, node)  # input should be string here
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
    nl = utils.add_OP_simulation(netlist, node)  # input should be string here
    print("==add_Cload", nl)

def test_pycpice_op_sim():
    netlist = local_config.netlist_14
    result = utils.pyspice_op_sim(netlist, "vout1")  # input should be string here
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
    netlist, new_V, old_V= utils.modify_DC_bias(netlist,"VB1",False)
    print("==netlist\n",netlist)
    print("==new\n",new_V)
    print("==old\n",old_V)
    return 0

def test_find_OPAMP_num_from_file():
    path = "../material/dataset/tb_dataset"
    nums = utils.find_OPAMP_num_from_file(path) #amplifier
    print("# ", len(nums))
    print("nums = ",nums)
    return nums

def test_find_OPAMPs_without_clk():
    path = "../material/dataset/tb_dataset"
    # nums = utils.find_OPAMP_num_from_file(path)
    nums = local_config.num_amplifier_with_vin_vout
    # print("==nums\n",nums)
    SISO_nums = utils.find_OPAMPs_without_clk(path,nums)
    print("==SISO_nums\n",SISO_nums)
    print("==how much\n",len(SISO_nums))

def test_find_SISOs_from_OPAMPs():
    path = "../material/dataset/tb_dataset"
    # nums = utils.find_OPAMP_num_from_file(path)
    nums = local_config.num_amplifier_without_mixer_comparator_ports
    # print("==nums\n",nums)
    SISO_nums = utils.find_SISOs_from_OPAMPs(path,nums)
    print("SISO_nums = ",SISO_nums)
    print("# ",len(SISO_nums))

    
def test_find_ports_from_nums(nums):
    dataset_path = "../material/dataset/tb_dataset"
    
    ports2 = utils.find_ports_from_all(dataset_path,nums)  
    print("ports2\n",ports2)

def test_find_num_by_port_name(port = ["VB1"],nums = [4]):
    dataset_path = "../material/dataset/tb_dataset"
    result_nums = utils.find_num_by_port_name(dataset_path,port,nums)# for only SISO    
    print(port[0]," = ",result_nums, "# ",len(result_nums))


def test_find_RF_from_cir_pattern():
    dataset_path = "../material/dataset/tb_dataset"
    # port = ["VOUT1"]
    nums1 = utils.find_cir_with_pattern_from_1044cir(dataset_path,["L0"])
    
    print("# ", len(nums1))
    print(nums1)


def test_find_all():
    dataset_path = "../material/dataset/tb_dataset"
    # port = ["VOUT1"]
    n = utils.find_all(dataset_path)
    print("# ", len(n))
    print(n)


def test_find_cir_without_mos():
    dataset_path = "../material/dataset/tb_dataset"
    # port = ["VOUT1"]
    nums = utils.find_cir_without_pattern_from_1044cir(dataset_path,["nmos4", "pmos4", "npn"])
    print("# ", len(nums))
    print(nums)

def test_find_cir_without_vout():
    dataset_path = "../material/dataset/tb_dataset"
    # port = ["VOUT1"]
    port = ["VOUT1"]
    num_test = local_config.nums_with_transistors
    nums = utils.find_cir_without_pattern_from_1044cir(dataset_path,port,num_test)
    print("# ", len(nums))
    print(nums)

def test_find_num_from_class():
    nums =utils.find_num_from_class(1)
    print("# ", len(nums))
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
    clean_netlist = utils.modify_duplicate_component(raw_netlist)
    print(clean_netlist)

def test_find_cir_without_vdd():
    dataset_path = "../material/dataset/tb_dataset"
    # port = ["VOUT1"]
    port = ["VSS"]
    num_test = local_config.num_class_1 # only 621
    num_test = local_config.num_all#
    nums = utils.find_cir_without_pattern_from_1044cir(dataset_path,port,num_test)
    print("# ", len(nums))
    print(nums)
def test_pyspice_sim(nl = local_config.nl_feb24):
    # nl = local_config.nl_feb23_wuhu
    utils.delete_all_files(local_config.output_path) # delete all previous output to avoid confusion
    
    utils.pyspice_op_sim_simple(nl)
    # success = utils.pyspice_op_sim(nl)
    # if success["success"]:
    #     print("Simulation successful!")
    # else:
    #     print("Simulation failed with message:", success["message"])
    success = utils.pyspice_op_sim_final(nl)
    if success["success"]:
        print("Simulation successful!")
    else:
        print("Simulation failed with message:", success["message"])

def test_run_ngspice_direct(nl = local_config.nl_feb24):
    # Write the netlist to a temporary file
    success = utils.run_ngspice_direct(nl)
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
def test_calculate_gain_bandwidth(path_gain = "./1genai/output/ac_gain.csv"):
    # Example data (replace with actual data from your simulation)
    path_psrr = "./1genai/output/ac_psrr.csv"
    path_noise = "./1genai/output/noise.csv"
    path_trans = "./1genai/output/tran_slew.csv"
    spice_result = utils.SpiceResult(path_gain, path_psrr, path_noise, path_trans)
    gain = spice_result.get_dc_gain()
    bandwidth = spice_result.get_bandwidth()
    pm = spice_result.get_gain_margin()
    gm = spice_result.get_phm()
    psrr = spice_result.get_psrr()
    inoise = spice_result.get_in_equivalent_noise()
    slew_rate = spice_result.get_slew_rate()
    # print("==freq", spice_result.mag_db[0])
    # print("==freq", spice_result.mag_db[-1])
    print(f"DC Gain: {gain} dB")
    print(f"Bandwidth: {bandwidth} Hz")
    print(f"Phase Margin: {pm} degrees")
    print(f"Gain Margin: {gm} dB")
    print(f"PSRR: {psrr} dB")
    print(f"Input Equivalent total Noise: {inoise} V")
    print(f"Slew Rate: {slew_rate} V/s")

    
    # results['dc_gain'] = df.iloc[0, 1]
    # print(f"DC Gain: {results.dc_gain} dB")
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
# test_find_num_by_port_name(["VCLK1"],local_config.num_amplifier_included_with_VCLK_and_so_on)
# test_find_cir_without_out()
# test_find_RF_from_cir_pattern()
# test_find_all()
# test_find_cir_without_mos()
# test_find_num_from_class()
# test_modify_duplicate_component()
# test_find_cir_without_vdd()
# test_pyspice_sim(local_config.nl_feb26)
# test_run_ngspice_direct(local_config.nl_feb24)
# test_check_output_files()
test_calculate_gain_bandwidth("./1genai/output/ac_gain.csv")

end_time = time.perf_counter()

# endregion

# utils.difference_of_nums(local_config.num_amplifier_without_mixer_comparator_ports, local_config.num_amplifier_included_with_VCLK_and_so_on)
# utils.difference_of_nums( local_config.num_amplifier_included_with_in_out,local_config.num_amplifier_without_mixer_comparator_ports)
# utils.difference_of_nums( local_config.num_all, local_config.num_no_mos)

  

print(f"Execution time: {end_time - start_time:.6f} seconds")
# test_pycpice_op()
"""
VDD
R
VDD/2
M1 B:0
VINCM/2
VSS B:VDD
"""
