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

Also, the netlist is simply checked for differential output: {is_diff}. If it is True, the netlist is very likely to be differential output. Do not use DC gain but DM gain for measurement!

Your goal is to complete simulation of the netlist and make sure the result netlist can be simulated and without errors. You should output the complete netlist, tell whether it is differential output or not, a list of required specifications and corresponding simulation files for measurement. The measurement will be done by following agents.
### Here are some rules:
[CRITICAL INSTRUCTION]: You must ONLY simulate and analyze the specifications explicitly required in the requirement. 
Do NOT assume, infer, or add any other measurements unless they are explicitly required by the requirement, even if they show in the table.

0. Check whether the circuit needs a load. If the circuit does not have a load, add a capacitor load. Example: 
.param Cload=10p 
Cload VOUT1 VSS {{Cload}} 
1. When it comes to the transistors parameters, patterns like w={{}} are not allowed. the curly brackets cause error. It should be w= a variable. The variable is assigned a value using .param. So, when there is =, do not use {{}}

2. When it comes to passive components like capacitor, it must have {{}} with a variable inside the brackets.
example: Cload VOUT1 VSS {{Cload}} 

3. You should read category requirement and add relevant simulations needed. But, calculation/measurement of specification will be done by following agent. So the simulation data format is important! Try example output first!

4. The netlist file should also write the required data to a file. The path should include the circuit number! Also, for ac_gain, use v(VOUT1) since the following measurement agent will use this format.. Using vdb(VOUT1) or vp(VOUT1) is incorrect.
In this example, the VOUT1 is the output node. Example:
* for gain
ac dec 10 1 {f_end}
{line_wrdata_path_num}/ac_gain.csv v(VOUT1)


5. ONE COMMAND PER LINE: Every '.param', '.model', or component must start on a NEW line. 
   - BAD: .param VDD=1.2 .param W=1u
   - GOOD: 
     .param VDD=1.2
     .param W=1u
6. If noise is required, use noise_total. Do not combine them. NEVER write two wrdata lines for noise in the same netlist.
    6a. If equivalent input totoal integrated noise is needed: To get the single value of total noise, use:
    noise v(VOUT1) vin dec 10 1 {f_end}
    {line_wrdata_path_num}/noise.csv inoise_total

7. If AC gain is required, use DC gain and UGBW. If phase response is required, use Phase Margin.

8. For slew rate transient analysis, example:  
vin VIN1 VSS dc=vcm ac=1.0 PULSE({{-VDD*0.5}} {{VDD*0.5}} trf trf trf {{0.5*period-trf}} period)
tran 50n 30u
{line_wrdata_path_num}/tran_SR.csv v(VOUT1)

9. For differential input, the input can be like this:
Vinput aid VSS dc=0.0 ac=1.0 PULSE({{-VHIGH*0.5}} {{VHIGH*0.5}} trf trf trf {{0.5*period-trf}} period)
ein1 net1 VCM aid 0 0.5
ein2 net2 VCM aid 0 -0.5

10. For differential output circuits, use differential mode gain instead of AC gain (single port) .
Also, the simulation should simulate the output separately for CM gain and DM gain. This is the format for later measurement.
Example:
{line_wrdata_path_num}/ac_gain.csv v(VOUT1) v(VOUT2)



12. You must always add current simlation. Single VDD current is enough.
Example:
op
{line_wrdata_path_num}/current.csv i(vdd)
11. 
13. Also, check whether there is CMFB stability in specifications. If there is CMFB LOOP, add simulation for it.
Example:
* CMFB Loop Injection Points
Lloop net29_sense net29_gate 1G
Cloop net29_gate loop_inj 1G
Vi loop_inj 0 dc=0 ac=1

alter vdm ac=0
ac dec 10 1 {f_end}
{line_wrdata_path_num}/cmfb_stb.csv v(net29_sense) v(net29_gate)

14. If output balance is required, use AC simulation since phases are required to see the balance.






18. If slew rate is needed, example:
tran 10n 20u
{line_wrdata_path_num}/tran_sr.csv v(VOUT1)    

### General Netlist Rules:

0. **Circuit requirements**: This is a amplifier. Ensure it has proper biasing network, feedback path, and current generation mechanism.
1. **Differential check**: There are 3 types of circuits: single-ended (SISO), fully differential (DIDO) and differential input single-ended output (DISO).
2. **CMFB stability**: Set to false for bandgap references (they don't typically use CMFB loops).
3. **Load**: Add load capacitance if not present (e.g., Cload=10p at output)
4. **Transistor parameters**: Use `.param` variables without curly brackets on the component line. WRONG: `w={{}}` CORRECT: `w=wp1` with `.param wp1=1u`
5. **Passive components**: Capacitors and resistors MUST use curly brackets with variables. CORRECT: `R0 node1 node2 {{r0}}` with `.param r0=1k`
6. **Data output format**: Each measurement must write to a unique CSV file with the circuit number in path! Lines MUST be kept : 'set units=degrees' and 'set wr_vecnames'!
7. **ONE command per line**: Every `.param`, `.model`, and component definition must start on a NEW line.
8. **Single noise method**: If noise is needed, use ONLY ONE noise specification (`onoise_total` or `inoise_total` ).
9. **Comments**: Remember to add short comments to tell the purpose of each simulation. Example: *current matching 
10. **Format**: If subcircuit device name does not fit the format, change the device name like (I1 net7 net4 VDD VSS INVERTER) should be changed to (X1 net7 net4 VDD VSS INVERTER) because it's a subcircuit. 
    - alter source from DC to trans is NOT allowed. Should define it outsice already WRONG:    alter @vla1[pulse] = [ 0 1.2 10n 50p 50p 1n 100n ]
    - DO NOT EXHAUSTIVELY RESET ALTER COMMANDS: Only use 'alter' when necessary since the simulation is sequential, so do the effect of alter. 
11. **MATCH THE AC MAGNITUDES STRICTLY TO EXPECTED PARSING**: When setting up differential mode AC sweeps, standard practice is applying 'ac 1' globally or assigning 0.5 and -0.5 on the unified differential input network branches. Avoid custom, overly complex math definitions inside the .control segment unless explicitly asked.
12. **KEEP SIMULATION SETUP MINIMAL (NO DUMMY SOURCES)**:
    - Do not generate standalone dummy tracking sources (e.g., dummy_diff_in, dummy_cm_in) or flat pulse lines to establish DC bias. 
    - Always prioritize using the E-source behavioral modeling approach (ein1/ein2 linked to a central vdm/vcm setup) as shown in Rule 9. It is cleaner and scales to all AC/Tran analyses without needing complex resetting.
    - Ideal block is accetable if it is not a big difference to the result.   
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
    


