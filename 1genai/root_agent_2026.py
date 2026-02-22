from google import genai
from google.genai import types

# import os
from pydantic import BaseModel, Field
from typing import List

######################
# local import
import local_config
import utils
import tools


######################
# structure output
######################
class NetlistFlow(BaseModel):
    netlist: str = Field(description="The circuit netlist.")
    V_DC_to_change: List[str] = Field(
        description="The DC bias like VB or VINCM to be tuned."
    )
    raise_V: List[bool] = Field(
        description="If it is true, increase the voltage"
    )
    reason_for_nodes: List[str] = Field(
        description="The corresponding reason to change the bias."
    )

# initiation

# cir_num = input() 
def test_make_cir_sim(cir_num):
    cir_path = local_config.dataset_path + f"/{cir_num}/{cir_num}.cir"
    print("==cir_path\n", cir_path)

    circuit_string = utils.get_file_to_str(cir_path)  
    # print("==circuit_string\n",circuit_string)
    circuit_string = utils.modify_duplicate_component(circuit_string)
    client = genai.Client(api_key=local_config.GOOGLE_API_KEY)
    vdd = 1.2  # this is retrieved from LLM
    circuit_string = utils.clean_netlist(circuit_string)# add .include here
    circuit_string = utils.add_params(circuit_string)
    circuit_string = utils.add_DC_source(circuit_string)

    circuit_string = utils.add_C_load(circuit_string)
    netlist = utils.add_OP_simulation(circuit_string)
    # print("==cir_str\n", netlist)


    # simulation
    sim_output = utils.pyspice_op_sim(netlist, "vout1")
    if sim_output["success"]:
        # print(sim_output["data"])
        a = 1
    else:
        
        print(sim_output["message"])
        raise RuntimeError
for i in local_config.num_class_1:
    if i <= 917:
        continue
    test_make_cir_sim(i)
    utils.test_delay(1)
# a = local_config.num_class_1.index(167)
# # print(a)
# test_make_cir_sim(a)


# Example usage:
