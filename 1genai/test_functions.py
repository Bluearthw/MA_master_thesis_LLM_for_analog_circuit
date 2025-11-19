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
        print("==clean\n",circuit_string)
        return circuit_string
        


def test_add_params(netlist):
#     netlist = """
# **== imcomplete cir file:
# .include "./1genai/data/45nm.sp"
# M1 VOUT2 VIN2 IB1 VSS nmos
# M0 VOUT1 VIN1 IB1 VSS nmos
# M3 VOUT2 VB1 VDD VDD nmos
# M2 VOUT1 VB1 VDD VDD nmos
# R1 VDD VOUT1
# R0 VDD VOUT2
#     """
    # lines = netlist # does not work, need to split first
    lines = netlist.strip().split('\n')# , add this line if the netlist is not identified as lines
    # print(netlist)
    nl = utils.add_params(lines)
    print("==add",nl)

test_add_params(test_clean()) 