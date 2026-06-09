from google import genai

# import os
# import sys

######################
# local import
from genai_agent import local_config
from genai_agent import tools
from genai_agent.workflows import sim_debug_meas_loop
from utils import gen_utils as gen_utils

path_output = local_config.path_output


def test_make_cir_sim(cir_num, path_output_num, category_str, netlist, has_input, trimmed_spec_table, is_diff):
           
    struc = add_sim_agent(netlist, category_str, cir_num, trimmed_spec_table, is_diff)
    print("struc=", struc)
    target_dc_vout = struc.target_dc_vout
    target_dc_vout = gen_utils.user_modify_input("Target DC Output Voltage", target_dc_vout)

    netlist = struc.netlist
    print("netlist_after_add_sim_agent=", netlist)
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
    
    
    data_for_dut_yaml = (is_differential_output, has_input, target_dc_vout)

    print("Combined measurement results:", combined_results)
    return combined_results, struct_path_id, path_netlist, spec_sims, data_for_dut_yaml#, cmfb_struct_path_id
    
def add_sim_agent(netlist, category,cir_num=4, trimmed_spec_table=None, is_diff=False):
    line_wrdata_path_num = "wrdata " + path_output + str(cir_num)
    
    client = gen_utils.get_client()
    f_end= "1T"
    contents = f"""You are an expert Analog IC Designer and NGSpice Specialist. You are given an incomplete netlist : {netlist}, a circuit number {cir_num}, a table of specifications and their IDs to look up : {trimmed_spec_table}, and a brief requirement about this type of circuit : {category}.

Also, previous about differential output check is given: {is_diff}. If it is True: 1, the netlist is very likely to be differential output. 2, do not use DC gain but DM gain for measurement!

Your goal is to complete simulation setup for amplifier circuit. The netlist must be fully simulated without errors. You should output:
1. The complete, ready-to-run netlist
2. Whether the output is differential (true/false)
3. A list of required specifications and corresponding simulation file paths for measurement
4. Whether CMFB stability check is needed (typically false for single output circuits)

### Here are some rules:

0. Gain example, the VOUT1 is the output node. Example:* for gain
ac dec 10 1 {f_end}
{line_wrdata_path_num}/ac_gain.csv v(VOUT1)

1. If noise is required, example:
noise v(VOUT1) vin dec 10 1 {f_end}
{line_wrdata_path_num}/noise.csv inoise_total

2. If AC gain is required, use DC gain and UGBW. If phase response is required, use Phase Margin.

3. For slew rate transient analysis, example:  
vin VIN1 VSS dc=vcm ac=1.0 PULSE({{-VDD*0.5}} {{VDD*0.5}} trf trf trf {{0.5*period-trf}} period)
tran 50n 30u
{line_wrdata_path_num}/tran_SR.csv v(VOUT1)

4. For differential input, the input can be like this:
Vinput aid VSS dc=0.0 ac=1.0 PULSE({{-VHIGH*0.5}} {{VHIGH*0.5}} trf trf trf {{0.5*period-trf}} period)
ein1 net1 VCM aid 0 0.5
ein2 net2 VCM aid 0 -0.5

5. For differential output circuits, use differential mode gain instead of AC gain (single port) .
Also, the simulation should simulate the output separately for CM gain and DM gain. This is the format for later measurement.
Example:
{line_wrdata_path_num}/ac_gain.csv v(VOUT1) v(VOUT2)


6. Always add current simlation. Single VDD current is enough.
Example:
op
{line_wrdata_path_num}/current.csv i(vdd)

7. If there is CMFB LOOP, add simulation for it.
Example:
* CMFB Loop Injection Points
Lloop net29_sense net29_gate 1G
Cloop net29_gate loop_inj 1G
Vi loop_inj 0 dc=0 ac=1

alter vdm ac=0
ac dec 10 1 {f_end}
{line_wrdata_path_num}/cmfb_stb.csv v(net29_sense) v(net29_gate)

8. If output balance is required, use AC simulation since phases are required to see the balance.

9. If slew rate is needed, example:
tran 10n 20u
{line_wrdata_path_num}/tran_sr.csv v(VOUT1)    

### General Netlist Rules:

0. **Circuit requirements**: This is a amplifier. Ensure it has proper biasing network, feedback path, and current generation mechanism.
1. **Differential check**: There are 3 types of circuits: single-ended (SISO), fully differential (DIDO) and differential input single-ended output (DISO).
2. **CMFB stability**: Set to false for bandgap references (they don't typically use CMFB loops).
{local_config.general_rules} 
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
                wait_sec = 40*retry_count  # Exponential backoff: 60s, 120s, 180s, etc.
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
    


