from google import genai
from google.genai import types

import os
import sys

from pydantic import BaseModel, Field
from typing import List # after python 3.9. before it is List
from pathlib import Path

######################
# local import
sys.path.append("./genai")
import genai_agent.data.local_config as local_config
import utils
import genai_agent.data.tools as tools
import genai_agent.workflows.debug_agent as debug_agent


def test_make_cir_sim(cir_num):
    
    path_cir = local_config.path_dataset + f"/{cir_num}/{cir_num}.cir"
    print("==cir_path\n", path_cir)
    path_output_num = local_config.path_output + f"{cir_num}/"
    circuit_string = utils.get_file_to_str(path_cir)  
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
    
    category_num = utils.find_cat_from_num(cir_num) # for now we only have one category. In the future, we can have more categories and the sim agent will read the requirement of the category and decide what simulations to add.
    path_category = local_config.path_category + f"{category_num}.md"
    # or the cat_num is already known, so just +"4.md"
    category_str = utils.get_file_to_str(path_category)
    
    struc = add_sim_agent(netlist, category_str, cir_num)
    netlist = struc.netlist
    spec_sims = struc.spec_sims
    print("==spec_sims", spec_sims)
    print("======sim netlist = ")
    print(netlist)
    
    
    counter = 0
    error_msg=[]
    # is_debug = False
    while True:
        sim_output = utils.run_ngspice_direct(netlist)
        print("=====sim output",sim_output)
        if sim_output["success"]: 
            #check files
            # gather all generated file paths; use a set to ensure uniqueness
            struct_path_id ={}# id: path
            for spec_sim in spec_sims:
                path_file = path_output_num + spec_sim.sim_file_name
                if os.path.exists(path_file):
                    print(f"File {path_file} exists.")
                    struct_path_id[spec_sim.spec_id] = path_file
                    
                else:
                    print(f"File {path_file} does not exist.")
                    raise RuntimeError(f"Expected output file {path_file} not found.")
            print("=== struct path id",struct_path_id)
            print("Simulation successful and output files verified!")
            # now `paths` contains only unique file paths, in the order they were encountered
            netlist_path = path_output_num + "final_netlist.cir"
            with open(netlist_path, "w") as f:
                f.write(netlist)
            measurement_results = utils.measuremnt(struct_path_id)
            # Run measurements using SpiceResult helpers
            
            print("Measurement results:", measurement_results)
            # return the unique paths for callers that care
            return measurement_results
            

        else:
            print(f"==================bug found!!!!======={counter}===============")
            error_msg.append(f"iteration{counter}:")
            error_msg.append(sim_output["message"]+"")
            error_msg_input = "\n".join(error_msg)
            print(error_msg_input)
            utils.test_delay(30)  # Wait 10 seconds before retrying
            struct_debug = debug_agent.debug_agent_flow(netlist, error_msg_input,cir_num)
            netlist = struct_debug.netlist
            spec_sims = struct_debug.spec_sims
            error_msg.append("fixing info:\n"+struct_debug.fix_info)
            
            # is_debug = True
        counter+=1
        if counter > 5:
            raise RuntimeError("Too many iterations in debug-sim loop. Something might be wrong.")
            # print("Too many iterations in debug-sim loop. Something might be wrong.")
    
    
def add_sim_agent(netlist, category,cir_num=4):
    client = gen_utils.get_client()
    contents = f"""You are an expert Analog IC Designer and NGSpice Specialist. You are given an incomplete netlist : {netlist}, a circuit number {cir_num}, a table of specifications and their IDs : {local_config.table_specs_id}, and a brief requirement about this type of circuit : {category}.
Your goal is to complete simulation of the netlist and make sure the result netlist can be simulated and without errors. You should output the complete netlist and the list of specifications and corresponding simulation files needed for measurement. The measurement will be done by following agents.
### Here are some rules.
0. Check whether the circuit needs a load. If the circuit does not have a load, add a capacitor load. Example: 
.param Cload=10p 
Cload VOUT1 VSS {{Cload}} 
1. When it comes to the transistors parameters, patterns like w={{}} are not allowed. the curly brackets cause error. It should be w= a variable. The variable is assigned a value using .param. So, when there is =, do not use {{}}

2. When it comes to passive components like capacitor, it must have {{}} with a variable inside the brackets.

3. You should read category requirement and add relevant simulations needed. But, calculation/measurement of specification will be done by following agent.

4. The netlist file should also write the required data to a file. The path should include the circuit number! Also, for ac_gain, use v(VOUT1) since the following measurement agent will use this format.. Using vdb(VOUT1) or vp(VOUT1) is bad 
Example:
* for gain
ac dec 10 1 100G
wrdata ./1genai/output/{cir_num}/ac_gain.csv v(VOUT1)
In this example, the VOUT1 is the output node.

5. ONE COMMAND PER LINE: Every '.param', '.model', or component must start on a NEW line. 
   - BAD: .param VDD=1.2 .param W=1u
   - GOOD: 
     .param VDD=1.2
     .param W=1u
6. You must provide exactly one noise reporting method. Do not combine them. NEVER write two wrdata lines for noise in the same netlist.
    6a. If equivalent input totoal integrated noise is needed: To get the single value of total noise, use:
    noise v(VOUT1) vin dec 10 1 100G
    wrdata ./1genai/output/{cir_num}/noise.csv inoise_total

    6b. If equivalent input noise spectrum is needed: To get the noise vs. frequency curve, use:
    noise v(VOUT1) vin dec 10 1 100G
    wrdata ./1genai/output/{cir_num}/noise.csv inoise_spectrum 

8. If transient analysis is needed, there is an example:  
vin VIN1 VSS dc=vcm ac=1.0 PULSE({{-VDD*0.5}} {{VDD*0.5}} trf trf trf {{0.5*period-trf}} period)
tran 50n 30u
wrdata ./1genai/output/{cir_num}/tran_SR.csv v(VOUT1)

9. For differential input, the input can be like this:
Vinput aid VSS dc=0.0 ac=1.0 PULSE({{-VHIGH*0.5}} {{VHIGH*0.5}} trf trf trf {{0.5*period-trf}} period)
ein1 net1 VCM aid 0 0.5
ein2 net2 VCM aid 0 -0.5
 """
    

    max_retries = 5  # Optional: prevent infinite loops if the server is truly down
    retry_count = 0
    
    while True:
        try:
            response = client.models.generate_content(
                model=local_config.agent_model,
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": tools.Struct_flow,
                },
            )
            # If successful, return the parsed data
            return response.parsed

        except Exception as e:
            # Check if the error is a 503 (Service Unavailable)
            # Note: Depending on your library version, 'e' might have a .code or .status_code
            error_msg = str(e)
            
            if "503" in error_msg or "ResourceExhausted" in error_msg:
                retry_count += 1
                wait_sec = 30*retry_count  # Exponential backoff: 60s, 120s, 180s, etc.
                print(f"Model busy (503). Retry #{retry_count}. ")
                utils.test_delay(wait_sec)  # Wait before retrying
            elif "429" in error_msg or "TooManyRequests" in error_msg:
                retry_count += 1
                wait_sec = 120*retry_count  # Exponential backoff: 60s, 120s, 180s, etc.
                print(f"Rate limit exceeded (429). Retry #{retry_count}. ")
                utils.test_delay(wait_sec)  # Wait before retrying
            else:
                # If it's a different error (like a syntax error in your code), 
                # we want to see it immediately rather than looping.
                print(f"An unexpected error occurred: {e}")
                raise e
        if retry_count >= max_retries:
            raise RuntimeError("Max retries reached. The model may be unavailable.")

    #out of while True and files exist.
# def measuremnt(spice_result, path, files):
    

test = local_config.num_class_7[:10]

num = 155
isLoop = True

if isLoop:
    for i in test:
        print("===========",i)

        # Define the directory path
        
        output_dir = Path(f"./1genai/output/{i}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create the directory
        # parents=True: creates ./1genai/output/ if they don't exist
        # exist_ok=True: doesn't crash if the folder "9" already exists
        test_make_cir_sim(i)
        utils.test_delay(30)
else:    
    output_dir = Path(f"./1genai/output/{num}")
    output_dir.mkdir(parents=True, exist_ok=True)
    unique_files = test_make_cir_sim(num)
    print("unique simulation files:", unique_files)