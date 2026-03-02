from google import genai
from google.genai import types

import os
from pydantic import BaseModel, Field
from typing import List # after python 3.9. before it is List

######################
# local import
import local_config
import utils
import tools
import debug_agent

######################
# structure output
######################
# class Struct_sim_task(BaseModel):
#     name: str = Field(description="The name of the simulation. It contains simulation name and what specs it is for. e.g., 'ac_gain'.")
#     reason: str = Field(description="The engineering justification for this sim.")
   # category_requirement: str = Field(description="The description and requirement of this type of circuit")
# initiation


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
    category = local_config.category_1_request # for now we only have one category. In the future, we can have more categories and the sim agent will read the requirement of the category and decide what simulations to add.
    struc = add_sim_agent(netlist, category)
    print("==spec_sims", struc.spec_sims)
    netlist = struc.netlist
    spec_sims = struc.spec_sims
    print("======sim netlist = ",netlist)
    counter = 0
    # is_debug = False
    while True:
        sim_output = utils.pyspice_op_sim_final(netlist)
        print("=====sim output",sim_output)
        if sim_output["success"]: 
            #check files
            for spec_sim in spec_sims:
                file_path = local_config.output_path + spec_sim.sim_file_name 
                if os.path.exists(file_path):
                    print(f"File {file_path} exists.")
                    
                else:
                    print(f"File {file_path} does not exist.")
                    raise RuntimeError(f"Expected output file {file_path} not found.")
            print("Simulation successful and output files verified!")
            measurement_results = measuremnt(spec_sims)
            # Run measurements using SpiceResult helpers
            print("Measurement results:", measurement_results)
            

            break # this is for while True
        else:
            print("==================bug found!!!!======================")
            utils.test_delay(60)  # Wait 10 seconds before retrying
            struct_debug = debug_agent.debug_agent(netlist, sim_output["message"])
            netlist = struct_debug.netlist
            spec_sims = struct_debug.spec_sims
            # is_debug = True
        counter+=1
        if counter > 5:
            raise RuntimeError("Too many iterations in debug-sim loop. Something might be wrong.")
            # print("Too many iterations in debug-sim loop. Something might be wrong.")
    
    
def add_sim_agent(netlist, category):
    client = genai.Client(api_key=local_config.GOOGLE_API_KEY)
    contents = f"""You are an experienced amplifier designer. You are given an incomplete netlist : {netlist}, and a brief requirement about this type of circuit : {category}.
You need to complete simulation of the netlist and make sure the result netlist can be simulated and without errors. 
Here are some rules.
0. If the circuit already has a load, do not add more loads. If the circuit does not have a load, add a capacitor load. Example: 
.param Cload=10p 
Cload VOUT1 VSS {{Cload}} 
1. When it comes to the transistors parameters, patterns like w={{}} are not allowed. the curly brackets cause error. It should be w= a variable. The variable is assigned a value using .param. So, when there is =, do not use {{}}
2. When it comes to passive components like capacitor, it must have {{}} with a variable inside the brackets.
3. You should read category requirement and add relevant simulations needed. But, calculation/measurement of specification will be done by following agent.
4. The netlist file should also write the required data to a file. Example:
* for gain
ac dec 10 1 10G
wrdata ./1genai/output/ac_gain.csv v(VOUT1)
In this example, the VOUT1 is the output node.
5. The output netlist must be line by line. e.g., 
.param VDD=1.2
.param w1=0.5u l1=90n m1=1
It must not be like this: Simulation\n.param VDD=1.2\n.param w1=0.5u ......
6, In NGSpice, the noise command produces two separate plots: 'noise1' for spectral density and 'noise2' for integrated noise. So, 'noise1.onoise_spectrum' (output refer noise) or 'noise1.inoise_spectrum' (input equivalent noise) can be tried.  """
  
    max_retries = 5  # Optional: prevent infinite loops if the server is truly down
    retry_count = 0
    
    while True:
        try:
            response = client.models.generate_content(
                model=local_config.agent_model3,
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
            else:
                # If it's a different error (like a syntax error in your code), 
                # we want to see it immediately rather than looping.
                print(f"An unexpected error occurred: {e}")
                raise e
        if retry_count >= max_retries:
            raise RuntimeError("Max retries reached. The model may be unavailable.")

    #out of while True and files exist.
# def measuremnt(spice_result, path, files):
def measuremnt(spec_sims):
    """Run measurements based on produced simulation files.

    Args:
        spec_sims: list of Struct_specs_sim objects describing sims produced.
        output_path: folder where sim CSV files are written (ends with / or \\).

    Returns:
        dict of computed metrics.
    """
    # try:
                
    #     measurement_results = measuremnt(spec_sims)
    # except Exception as e:
    #     print("Measurement failed:", e)

    # collect sim filenames
    results = {}
    output_path = local_config.output_path
    # If we have both gain and psrr files, use SpiceResult to compute common metrics
    paths = {
        "ac_path": None,
        "inoise_path": None,
        "sr_path": None,
        "ac_psrr_path": None
    }
    for spec_sim in spec_sims:
        if spec_sim.spec_id == 0:
            paths["ac_path"] = os.path.join(output_path, spec_sim.sim_file_name)
        elif spec_sim.spec_id == 1 and paths["ac_path"]:
            continue
        elif spec_sim.spec_id == 1 and not paths["ac_path"]:
            paths["ac_path"] = os.path.join(output_path, spec_sim.sim_file_name)
        elif spec_sim.spec_id == 2:
            paths["ac_psrr_path"] = os.path.join(output_path, spec_sim.sim_file_name)
        elif spec_sim.spec_id == 3:
            paths["inoise_path"] = os.path.join(output_path, spec_sim.sim_file_name)
        elif spec_sim.spec_id == 4:
            paths["sr_path"] = os.path.join(output_path, spec_sim.sim_file_name)
        elif spec_sim.spec_id == 5 and paths["ac_path"]:
            continue
        elif spec_sim.spec_id == 5 and not paths["ac_path"]:
            paths["ac_path"] = os.path.join(output_path, spec_sim.sim_file_name)
        elif spec_sim.spec_id == 6 and paths["ac_path"]:
            continue
        elif spec_sim.spec_id == 6 and not paths["ac_path"]:
            paths["ac_path"] = os.path.join(output_path, spec_sim.sim_file_name)
        else:
            raise ValueError(f"Unknown spec_id {spec_sim.spec_id} in spec_sims.")


    
    spice_res = utils.SpiceResult(paths["ac_path"], paths["ac_psrr_path"], paths["inoise_path"], paths["sr_path"])

    results['dc_gain'] = float(spice_res.get_dc_gain())
    # results['max_gain_db'] = float(spice_res.get_max_gain())
    results['bandwidth'] = float(spice_res.get_bandwidth())
    results['input_ref_total_noise'] = float(spice_res.get_in_equivalent_noise())
    results['phase_margin'] = float(spice_res.get_phm())
    results['gain_margin'] = float(spice_res.get_gain_margin())
    results['slew_rate'] = float(spice_res.get_slew_rate())
    results["psrr"] = float(spice_res.get_psrr())
    return results
    

def test_debug_agent():
    success = {"success": False, "message": "Error: no such vector onoise_spectrum"}
    if success["success"]:
        print("Simulation successful!")
    else:
       debug_agent.debug_agent(local_config.nl_feb24, success["message"])
# test_debug_agent()

# for i in local_config.num_class_1:
#     if i <= 917:
#         continue
#     test_make_cir_sim(i)
#     utils.test_delay(1)
test_make_cir_sim(local_config.num_class_1[1])