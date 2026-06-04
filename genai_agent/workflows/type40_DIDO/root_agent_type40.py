from google import genai

import os
import sys

######################
# local import
from genai_agent import local_config
from genai_agent import tools
from genai_agent.workflows import sim_debug_meas_loop

from utils import gen_utils as gen_utils
from utils import saving
from ngspice_interface import dut_testbench

path_output = local_config.path_output


def test_make_cir_sim(cir_num, path_output_num, category_str, netlist, has_input, trimmed_spec_table):
           
    struc = add_sim_agent(netlist, category_str, cir_num, trimmed_spec_table)
    target_dc_vout = struc.target_dc_vout
    target_dc_vout = gen_utils.user_modify_input("Target DC Output Voltage", target_dc_vout)

    netlist = struc.netlist
    netlist = gen_utils.ensure_data_format_settings(netlist)
    netlist = gen_utils.modify_ac_range_1T(netlist)
    spec_sims = struc.spec_sims
    is_differential_output = struc.is_diff
    is_CMFB = struc.is_CMFB
    for spec_sim in spec_sims:
        print("==spec_sims", spec_sim)
    print("======sim netlist = ")
    print(netlist)
    print(is_differential_output)
    print("is CMFB:", is_CMFB)
    
    # Simulate original netlist
    results_original, struct_path_id = sim_debug_meas_loop.sim_debug_measure_loop(netlist, spec_sims, cir_num, path_output_num, is_differential_output, target_dc_vout, has_input, is_CMFB)
    
    combined_results = {'original': results_original}
    path_netlist = path_output_num + "final_netlist.cir"
    gen_utils.save_str_to_file(netlist, path_netlist)
    
    # cmfb_struct_path_id = ""
    if is_CMFB:
        path = path_output + "cmfb_num.txt"
        with open(path, "a") as f:  # "a" opens the file in append mode
            f.write(f"{cir_num}\n")

    
    data_for_dut_yaml = (is_differential_output, has_input, target_dc_vout)

    print("Combined measurement results:", combined_results)
    return combined_results, struct_path_id, path_netlist, spec_sims, data_for_dut_yaml#, cmfb_struct_path_id
    
def add_sim_agent(netlist, category,cir_num=4, trimmed_spec_table=None):
    line_wrdata_path_num = "wrdata " + path_output + str(cir_num)
    client = genai.Client(api_key=local_config.GOOGLE_API_KEY_yong)
    f_end= "1T"
    contents = f"""You are an expert Analog IC Designer and NGSpice Specialist. You are given an incomplete netlist : {netlist}, a circuit number {cir_num}, a table of specifications and their IDs to look up : {trimmed_spec_table}, and a brief requirement about this type of circuit : {category}.
[CRITICAL INSTRUCTION]: You must ONLY simulate and analyze the specifications explicitly required in the requirement. 
Do NOT assume, infer, or add any other measurements unless they are explicitly required by the requirement, even if they show in the table.
Your goal is to complete simulation of the netlist and make sure the result netlist can be simulated and without errors. You should output the complete netlist, tell whether it is differential output or not, a list of required specifications and corresponding simulation files for measurement. The measurement will be done by following agents.
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
ac dec 10 1 {f_end}
{line_wrdata_path_num}/ac_gain.csv v(VOUT1)
In this example, the VOUT1 is the output node.

5. ONE COMMAND PER LINE: Every '.param', '.model', or component must start on a NEW line. 
   - BAD: .param VDD=1.2 .param W=1u
   - GOOD: 
     .param VDD=1.2
     .param W=1u
6. You must provide exactly one noise reporting method. Do not combine them. NEVER write two wrdata lines for noise in the same netlist.
    6a. If equivalent input totoal integrated noise is needed: To get the single value of total noise, use:
    noise v(VOUT1) vin dec 10 1 {f_end}
    {line_wrdata_path_num}/noise.csv inoise_total

    6b. If equivalent input noise spectrum is needed: To get the noise vs. frequency curve, use:
    noise v(VOUT1) vin dec 10 1 {f_end}
    setplot noise1
    {line_wrdata_path_num}/noise.csv inoise_spectrum 

8. If transient analysis is needed, there is an example:  
vin VIN1 VSS dc=vcm ac=1.0 PULSE({{-VDD*0.5}} {{VDD*0.5}} trf trf trf {{0.5*period-trf}} period)
tran 50n 30u
{line_wrdata_path_num}/tran_SR.csv v(VOUT1)

9. For differential input, the input can be like this:
Vinput aid VSS dc=0.0 ac=1.0 PULSE({{-VHIGH*0.5}} {{VHIGH*0.5}} trf trf trf {{0.5*period-trf}} period)
ein1 net1 VCM aid 0 0.5
ein2 net2 VCM aid 0 -0.5

10. If the circuit is differential output. Make sure the specification is correct.
Use differential mode gain instead of AC gain (single port) for differential output circuits.
Also, the simulation should simulate the output separately for CM gain and DM gain. This is the format for later measurement.
Example:
{line_wrdata_path_num}/ac_gain.csv v(VOUT1) v(VOUT2)

11. Also, you should pay attention to whether there is CMFB stability specification check. The following agent will make a new netlist if the CMFB stability is needed.

12. You must always add current simlation.
Example:
op
{line_wrdata_path_num}/dc_current.csv i(vdd)

13. If there is CMFB LOOP, add simulation for it. Be careful about 'alter'.
Example:
* CMFB Loop Injection Points
Lloop net29_sense net29_gate 1G
Cloop net29_gate loop_inj 1G
Vi loop_inj 0 dc=0 ac=1

alter vdm ac=0
ac dec 10 1 100G
{line_wrdata_path_num}/cmfb_stb.csv v(net29_sense) v(net29_gate)

"""
    

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
                wait_sec = 30*retry_count  # Exponential backoff: 60s, 120s, 180s, etc.
                print(f"Model busy (503). Retry #{retry_count}. ")
                gen_utils.test_delay(wait_sec)  # Wait before retrying
            elif "429" in error_msg or "TooManyRequests" in error_msg:
                retry_count += 1
                wait_sec = 120*retry_count  # Exponential backoff: 60s, 120s, 180s, etc.
                print(f"Rate limit exceeded (429). Retry #{retry_count}. ")
                gen_utils.test_delay(wait_sec)  # Wait before retrying
            else:
                # If it's a different error (like a syntax error in your code), 
                # we want to see it immediately rather than looping.
                print(f"An unexpected error occurred: {e}")
                raise e
        if retry_count >= max_retries:
            raise RuntimeError("Max retries reached. The model may be unavailable.")

    #out of while True and files exist.
# def measuremnt(spice_result, path, files):
    


