from google import genai
from google.genai import types
import os
import utils
from pydantic import BaseModel, Field
import local_config

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

def test_pycpice_op():
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
    print("==nums\n",nums)
    return nums

def test_find_SISO_V_from_OPAMPs():
    path = "../material/dataset/tb_dataset"
    nums = utils.find_OPAMP_num_from_file(path)
    # print("==nums\n",nums)
    SISO_nums = utils.find_SISO_V_from_OPAMPs(path,nums)
    print("==SISO_nums\n",SISO_nums)
    print("==how much\n",len(SISO_nums))
    return SISO_nums
def test_find_ports_from_all():
    dataset_path = "../material/dataset/tb_dataset"
    SISO_nums = test_find_SISO_V_from_OPAMPs()
    # ports = utils.find_ports_from_all(dataset_path)# all    
    ports2 = utils.find_ports_from_all(dataset_path,SISO_nums)# for only SISO    
    # if(ports == ports2): #it is not yes
    #     print("yes")
    # else:
        # print("ports",ports)
    print("ports2\n",ports2)
# test_clean()
# test_add_params()
# test_add_source()
# test_add_C_load()
# test_add_add_OP_simulation()
# test_modify_DC_bias()
test_find_OPAMP_num_from_file()
# test_find_SISO_from_OPAMPs()
# test_find_ports_from_all()

# test_pycpice_op()
"""
VDD
R
VDD/2
M1 B:0
VINCM/2
VSS B:VDD
"""
