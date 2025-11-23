from google import genai
from google.genai import types
import os
import utils
from pydantic import BaseModel, Field


def test_clean():
    for i in range(5, 80):
        cir_path = f"../material/dataset/tb_dataset/{i}/{i}.cir"
        # print(i)
        # print("cir_path",cir_path)
        if not os.path.isfile(cir_path):
            continue
        circuit_string = utils.get_file_to_str(
            cir_path,
            "**== imcomplete cir file:\n",
            '.include "./1genai/data/45nm.sp" \n',
        )
        circuit_string = utils.clean_netlist(circuit_string)
        print("==clean\n", circuit_string)
        return circuit_string


def test_add_params(netlist=""):
    netlist = """

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


# test_add_params()


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

# test_add_source()
def test_add_C_load(netlist=""):
    netlist = """
*params

.param VDD=1.2
.param w0=0.5u l0=90n m0=1
.param w1=0.5u l1=90n m1=1
.include "1genai/data/45nm.sp"
M0 VOUT1 VB1 VDD VDD pmos w=w0 l=l0 m=m0
M1 VOUT1 VIN1 VSS VSS nmos w=w1 l=l1 m=m1

Vdd VDD 0 dc=VDD

Vss VSS 0 dc=0
"""
    node = "VOUT1" # should be from the LLM
    nl = utils.add_C_load(netlist, node)  # input should be string here
    print("==add_Cload", nl)


def test_add_C_load2(netlist=""):
    netlist = """
*params


.param Cload=10p
.param VDD=1.2
.param w0=0.5u l0=90n m0=1
.param w1=0.5u l1=90n m1=1
.include "1genai/data/45nm.sp"
M0 VOUT1 VB1 VDD VDD pmos w=w0 l=l0 m=m0
M1 VOUT1 VIN1 VSS VSS nmos w=w1 l=l1 m=m1

Vdd VDD 0 dc=VDD

Vss VSS 0 dc=0

Cload VOUT1 VSS {Cload}
"""
    node = "VIN1" # should be from the LLM
    nl = utils.add_OP_simulation(netlist, node)  # input should be string here
    print("==add_Cload", nl)

