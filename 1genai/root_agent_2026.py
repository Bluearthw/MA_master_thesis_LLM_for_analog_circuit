from google import genai
from google.genai import types

# import os
from pydantic import BaseModel, Field
from typing import List # after python 3.9. before it is List

######################
# local import
import local_config
import utils
import tools


######################
# structure output
######################
class Struct_sim_task(BaseModel):
    name: str = Field(description="The name of the simulation. It contains simulation name and what specs it is for. e.g., 'ac_gain'.")
    reason: str = Field(description="The engineering justification for this sim.")
class Struct_flow(BaseModel):
    netlist: str = Field(description="The SPICE netlist. Use standard newlines (\\n) between every line.")
    sims : list[Struct_sim_task] = Field(description="simulations needed and why")
    sim_name : list[str] =Field(description="list of names of simulations")
    # category_requirement: str = Field(description="The description and requirement of this type of circuit")
class Struct_netlist(BaseModel):
    netlist: str = Field(description="The SPICE netlist. Use standard newlines (\\n) between every line.")
# initiation
agent_model = "gemini-3-flash-preview" 
# agent_model = "gemini-2.5-flash"
# cir_num = input() 
def test_make_cir_sim(cir_num):
    
    cir_path = local_config.dataset_path + f"/{cir_num}/{cir_num}.cir"
    print("==cir_path\n", cir_path)

    circuit_string = utils.get_file_to_str(cir_path)  
    # print("==circuit_string\n",circuit_string)
    circuit_string = utils.modify_duplicate_component(circuit_string) # remove duplicate component names like 2 C1 in 167
    circuit_string = utils.clean_netlist(circuit_string)# ADD .include here. remove (). nmos4' to 'nmos' and 'pmos4' to 'pmos'. REMOVE 'resistor' and 'capacitor'
    circuit_string = utils.add_params(circuit_string) #ADD .param. ADD w,l,m to mos. ADD {value} for R and C
    circuit_string = utils.add_DC_source(circuit_string)
    # print("==cir_str\n", circuit_string)

    # circuit_string = utils.add_C_load(circuit_string)# some does not need to add C load.
    # netlist = utils.add_OP_simulation(circuit_string)
    netlist = utils.add_control(circuit_string)
    print("==cir_str\n", netlist)
    category = """### 1. Single-Ended Baseband Voltage Amplifiers (Linear Gain Stages)
A fundamental gain block intended for signal conditioning, typically operating in the "small-signal" regime where linearity is assumed and crossover distortion is negligible. These circuits prioritize voltage gain accuracy, bandwidth, and feedback stability.

* **Ports:**
    * **Required:** **Exactly one** signal voltage input (High Impedance typical). *If a second signal input exists, it is Class 7 or 40.*
    * **Required:** Single voltage output (Medium/Low Impedance).
    * **Note:** Unlike RF amps, input impedance matching is rarely required; the focus is on voltage bridging ($Z_{in} \gg Z_{source}$).
* **Stimuli/Measurements:**
    * **Stimuli:** Small-signal AC voltage source; DC bias voltage.
    * **Measurements:**
        * **Voltage Gain ($A_v$) & Phase:** AC analysis to determine DC gain and the -3dB corner frequency.
        * **Stability (PM/GM):** **Critical.** Analysis of Phase Margin and Gain Margin to ensure the amplifier does not oscillate when placed in a feedback loop.
        * **PSRR:** AC analysis of supply rejection (often critical in baseband precision circuits). *(Note: CMRR is not applicable here as there is no accessible differential input pair).*
        * **Input-Referred Noise:** Voltage noise density ($nV/\sqrt{Hz}$) integration over the bandwidth.
        * **Slew Rate:** Transient analysis with a step response (strictly for settling time, not distortion).
* **Topologies:**
    * **Fundamental Stages:** Common-Source (CS), Common-Emitter (CE), Cascode, Telescopic Cascode, Folded Cascode.
    * **Multi-Stage:** Operational Amplifiers (Op-Amps) in open loop or fixed feedback configurations, OTA (Operational Transconductance Amplifiers).
    * **Internal Differential Structures:** 

 Includes circuits that use a **differential input pair internally** (e.g., an Op-Amp with feedback resistors or a self-biased reference on the inverting node) but **do not expose the second input** as a top-level port.
    * **Active Loads:** Current mirrors, active inductor loads (for bandwidth extension without RF tuning).
* **Rule:** The circuit is a **linear gain block** with a **Single-Input/Single-Output (SISO)** interface.
    * It is disqualified if it includes inductive source degeneration (indicates LNA).
    * It is disqualified if it relies on complementary switching devices for high-current output (indicates Push-Pull/Class AB).
"""
    add_sim_agent(netlist, category)
    # # simulation
    # sim_output = utils.pyspice_op_sim(netlist, "vout1")
    # if sim_output["success"]:
    #     # print(sim_output["data"])
    #     a = 1
    # else:
        
    #     print(sim_output["message"])
    #     raise RuntimeError

def add_sim_agent(netlist, category):
    client = genai.Client(api_key=local_config.GOOGLE_API_KEY)
    contents = f"""You are an experienced amplifier designer. You are given an incomplete netlist : {netlist}, and a brief requirement about this type of circuit : {category}.
You need to complete simulation of the netlist and make sure the result netlist can be simulated. 
Here are some rules.
0. If the circuit already has a load, do not add more loads. If the circuit does not have a load, add a capacitor load. Example: 
.param Cload=10p 
Cload VOUT1 VSS {{Cload}} 
1. When it comes to the transistors parameters, patterns like w={{}} are not allowed. the curly brackets cause error. It should be w= a variable. The variable is assigned a value using .param. 
2. When it comes to passive components like capacitor, it must have {{}} with a variable inside the brackets.
3. You should read category requirement and add relevant simulations needed. But, calculation/measurement of specification will be done by following agent.
4. The netlist file should also write the required data to a file. Example:
* for gain
ac dec 10 1 10G
wrdata ./1genai/output/ac_gain.csv v(VOUT1)

In this example, the VOUT1 is the output node.
    """
    response = client.models.generate_content(
    model=agent_model,
    contents=contents,
    config={
        "response_mime_type": "application/json",
        "response_schema": Struct_flow,
        # "response_json_schema": Struct_flow.model_json_schema(),
    },
    )
    str = response.parsed
    print(str.netlist)
    print(str.sims)
    print(str.sim_name)
    
# for i in local_config.num_class_1:
#     if i <= 917:
#         continue
#     test_make_cir_sim(i)
#     utils.test_delay(1)
# test_make_cir_sim(local_config.num_class_1[1])

def debug_agent(netlist, error_message):
    client = genai.Client(api_key=local_config.GOOGLE_API_KEY)
    contents = f"""You are an experienced amplifier designer. You are given a netlist : {netlist}, and an error message from simulation : {error_message}.
    Fix the netlist based on the error message so that it can be simulated well. 
"""
    response = client.models.generate_content(
    model=agent_model,
    contents=contents,
    config={
        "response_mime_type": "application/json",
        "response_schema": Struct_netlist,
        # "response_json_schema": Struct_flow.model_json_schema(),
    },
    )
    str = response.parsed
    print(str.netlist)
    
