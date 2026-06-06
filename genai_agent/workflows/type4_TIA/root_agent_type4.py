from google import genai
from google.genai import types

import os
import sys

from pydantic import BaseModel, Field
from typing import List # after python 3.9. before it is List
from pathlib import Path

######################
# local import
sys.path.append("./1genai")
import local_config
import utils
import tools
import debug_agent


def test_make_cir_sim(cir_num):
    
    path_cir = local_config.path_dataset + f"/{cir_num}/{cir_num}.cir"
    print("==cir_path\n", path_cir)
    path_output = local_config.path_output + f"{cir_num}/"
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
    print("==spec_sims", struc.spec_sims)
    netlist = struc.netlist
    spec_sims = struc.spec_sims
    print("======sim netlist = ",netlist)
    utils.save_str_to_file(netlist, path_output + "final_netlist.cir")
    
    counter = 0
    # is_debug = False
    while True:
        sim_output = utils.pyspice_op_sim_final(netlist)
        print("=====sim output",sim_output)
        if sim_output["success"]: 
            #check files
            # gather all generated file paths; use a set to ensure uniqueness
            struct_path_id ={}
            for spec_sim in spec_sims:
                path_file = path_output + spec_sim.sim_file_name
                if os.path.exists(path_file):
                    print(f"File {path_file} exists.")
                    struct_path_id[spec_sim.spec_id] = path_file
                    
                else:
                    print(f"File {path_file} does not exist.")
                    raise RuntimeError(f"Expected output file {path_file} not found.")
            print("=== struct path id",struct_path_id)
            print("Simulation successful and output files verified!")
            # now `paths` contains only unique file paths, in the order they were encountered
            netlist_path = path_output + "final_netlist.cir"
            with open(netlist_path, "w") as f:
                f.write(netlist)
            measurement_results = measuremnt(spec_sims, struct_path_id)
            # Run measurements using SpiceResult helpers
            
            print("Measurement results:", measurement_results)
            # return the unique paths for callers that care
            

        # else:
        #     print(f"==================bug found!!!!======={counter}===============")
        #     utils.test_delay(60)  # Wait 10 seconds before retrying
        #     struct_debug = debug_agent.debug_agent(netlist, sim_output["message"],cir_num)
        #     netlist = struct_debug.netlist
        #     spec_sims = struct_debug.spec_sims
        #     # is_debug = True
        counter+=1
        if counter > 5:
            raise RuntimeError("Too many iterations in debug-sim loop. Something might be wrong.")
            # print("Too many iterations in debug-sim loop. Something might be wrong.")
    
    
def add_sim_agent(netlist, category,cir_num=4):
    client = genai.Client(api_key=local_config.GOOGLE_API_KEY_yong)
    contents = f"""You are an expert Analog IC Designer and NGSpice Specialist. You are given an incomplete netlist : {netlist}, a circuit number {cir_num}, and a brief requirement about this type of circuit : {category}.
Your goal is to complete simulation of the netlist and make sure the result netlist can be simulated and without errors. 
### Here are some rules.
0. If the circuit already has a load, do not add more loads. If the circuit does not have a load, add a capacitor load. Example: 
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
6. In NGSpice, you can use inoise_total if the input integration noise is required.
Example for input refer total noise int egrated:
noise v(VOUT1) vin dec 10 1 100G
wrdata ./1genai/output/{cir_num}/noise.csv inoise_total
Or you can use inoise_spectrum if the noise spectrum is required. Example:
noise v(VOUT1) vin dec 10 1 100G
wrdata ./1genai/output/{cir_num}/noise.csv noise1.inoise_spectrum 

7. Also, there is an example about transient analysis. 
vin VIN1 VSS dc=vcm ac=1.0 PULSE({{-VDD*0.5}} {{VDD*0.5}} trf trf trf {{0.5*period-trf}} period)
tran 50n 30u
wrdata ./1genai/output/{cir_num}/tran_SR.csv v(VOUT1)

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
                wait_sec = 60*retry_count  # Exponential backoff: 60s, 120s, 180s, etc.
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
def measuremnt(spec_sims, struct_path_id):
    """Run measurements based on produced simulation files.

    Args:
        spec_sims: list of Struct_specs_sim objects describing sims produced.
        output_path: folder where sim CSV files are written (ends with / or \\).

    Returns:
        dict of computed metrics.
    """
    
    results = {}
    spice_res = utils.SpiceResultNew()

    # spec_id mapping: 0=DC Gain, 1=Bandwidth, 2=PSRR, 3=input noise, 4=slew rate, 5=gain margin, 6=phase margin
    for spec_id, path in struct_path_id.items():
        if spec_id == 0:  # AC gain analysis (contains frequency response)
            results['dc_gain'] = float(spice_res.get_dc_gain(path))
            results['phase_margin'] = float(spice_res.get_phm())
        elif spec_id == 1:  # Bandwidth (if separate from gain) or other AC sim
            results['bandwidth'] = float(spice_res.get_bandwidth(path))
        
        elif spec_id == 2:  # PSRR
            results["psrr"] = float(spice_res.get_psrr(path))
        
        elif spec_id == 3:  # input noise
            results['input_ref_total_noise'] = float(spice_res.get_in_equivalent_noise_from_total(path))
        
        elif spec_id == 7:  # input equivalent noise spectrum
            results['input_ref_noise_spectrum'] = spice_res.get_in_equivalent_noise_from_spectrum(path)
        
        elif spec_id == 4:  # slew rate
            results['slew_rate'] = float(spice_res.get_slew_rate(path))
        elif spec_id == 5:  # gain margin
            results['gain_margin'] = float(spice_res.get_gain_margin(path))
    
    return results
    

test = local_config.num_class_4_new

num = 236
loop = False

if loop:
    for i in test:
        print("===========",i)

        # Define the directory path
        
        output_dir = Path(f"./1genai/output/{i}")

        # Create the directory
        # parents=True: creates ./1genai/output/ if they don't exist
        # exist_ok=True: doesn't crash if the folder "9" already exists
        output_dir.mkdir(parents=True, exist_ok=True)
        test_make_cir_sim(43)
        utils.test_delay(60)
else:    
    output_dir = Path(f"./1genai/output/{num}")
    output_dir.mkdir(parents=True, exist_ok=True)
    unique_files = test_make_cir_sim(num)
    print("unique simulation files:", unique_files)