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


def test_make_cir_sim(cir_num, path_output_num, category_str, netlist, has_input, trimmed_spec_table):
    
    struc = add_sim_agent(netlist, category_str, cir_num, trimmed_spec_table)
    target_dc_vout = struc.target_dc_vout
    target_dc_vout = gen_utils.user_modify_input("Target DC Output Voltage", target_dc_vout)

    netlist = struc.netlist
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
    print(target_dc_vout)
    results_original, struct_path_id = sim_debug_meas_loop.sim_debug_measure_loop(netlist, spec_sims, cir_num, path_output_num, is_differential_output, target_dc_vout, has_input)
    
    combined_results = {'original': results_original}
    path_netlist = path_output_num + "final_netlist.cir"
    # gen_utils.save_str_to_file(netlist, path_netlist)
   
    
    data_for_dut_yaml = (is_differential_output, has_input, target_dc_vout)

    print("Combined measurement results:", combined_results)
    return combined_results, struct_path_id, path_netlist, spec_sims, data_for_dut_yaml
    
def add_sim_agent(netlist, category, cir_num=4, trimmed_spec_table=None):
    line_wrdata_path_num = "wrdata " + path_output + str(cir_num)
    client = genai.Client(api_key=local_config.GOOGLE_API_KEY_yong)
    # f_end = "1T"
    contents = f"""You are an expert Analog IC Designer and NGSpice Specialist. You are given a netlist for a charge pump circuit: {netlist}, circuit number {cir_num}, a table of specifications and their IDs: {trimmed_spec_table}, and detailed requirements: {category}.
Your goal is to complete the simulation setup for the charge pump circuit. The netlist must be fully simulated without errors. You should output:
1. The complete, ready-to-run netlist
2. Whether the output is differential (true/false)
3. A list of required specifications and corresponding simulation file paths for measurement
4. Whether CMFB stability check is needed (typically false for charge pump circuits)

### Charge Pump-Specific Rules and Measurements:
**Simulation Examples**:
1. **Current Matching**: Perform two separate DC sweeps of the output node to characterize the source and sink currents across the full compliance range.   
    - Simulation:   Phase A (Source): Force the UP logic input to VDD and the DN input to 0. Sweep a DC voltage source at the output (VCONT1) from 0 to VDD.   
                    Phase B (Sink): Force the DN logic input to VDD and the UP logic input to 0. Sweep the same DC voltage source at the output from 0 to VDD.   
    - Example:
    - Subcircuit can be removed or use ideal block if it is not needed. 
    * Declare helping netlist. The numbers can change if needed. 1.2 is VDD. 
    vgate_n net3 0 pulse(0   1.2 10ns 50ps 50ps 400ps 20ns) 
    vgate_p net4 0 pulse(1.2 0   10ns 50ps 50ps 400ps 20ns)

    vout_force VCONT1 0 dc=0.6
    .ic v(VCONT1) = 0.6
    .control
    ...
    * 1a. Measure Source Current (PMOS ON, NMOS OFF)
    alter vgate_p dc=0
    alter vgate_n dc=0
    dc vout_force 0 1.2 0.01
    - Output: {line_wrdata_path_num}/ source_current.csv i(vout_force)
    
    * 1b. Measure Sink Current (PMOS OFF, NMOS ON)
    alter vgate_p dc=1.2
    alter vgate_n dc=1.2
    dc vout_force 0 1.2 0.01
    - Output: {line_wrdata_path_num}/ sink_current.csv i(vout_force)

2. **Output Ripple**: Apply simultaneous, narrow, identical pulses to both `UP` and `DN` inputs to simulate a locked PFD state, and measure the peak-to-peak voltage variation on the output node with the load capacitor.
    - Simulation: narrow simultaneous pulses on UP and DN, transient analysis.
    - Output: {line_wrdata_path_num}/output_ripple.csv v(VOUT1)

3. **Voltage Compliance Range**: Sweep the DC voltage at the charge pump output node and measure the output current to determine the operating voltage range where sourced and sinked currents remain matched.
    - Simulation: Same as current matching, no more simulation needed.
    - Output: Same as current matching, use those 2 paths. So, there are 2 spec_sim terms.

4. **Average supply current**: Need to know the current for power. Since it is with clock, transient analysis is required.
    - Simulation: careful about the clock definition and the trans signal
    - Output: {line_wrdata_path_num}/current.csv vdd#branch

5. **subcircuit**: They can be removed and use ideal blocks. If needed, there are examples:
    
    .subckt INVERTER in out vdd vss
    B1 out vss v = (v(in) > (v(vdd)/2)) ? v(vss) : v(vdd)
    .ends INVERTER
    
    .subckt PFD clka clkb up dn vdd vss
    B1 up vss V=V(clka)
    B2 dn vss V=V(clkb)
    .ends


### General Netlist Rules:

0. **Load**: Add load capacitance if needed (e.g., Cload=10p at output)
1. **Transistor parameters**: Use `.param` variables without curly brackets on the component line. WRONG: `w={{}}` CORRECT: `w=wp1` with `.param wp1=1u`
2. **Passive components**: Capacitors and resistors MUST use curly brackets with variables. CORRECT: `R0 node1 node2 {{r0}}` with `.param r0=1k`
3. **Circuit requirements**: This is a charge pump circuit. Ensure it has proper switching network, capacitors, and control logic for voltage multiplication.
4. **Data output format**: Each measurement must write to a unique CSV file with the circuit number in path! Lines MUST be kept : 'set units=degrees' and 'set wr_vecnames'!
5. **ONE command per line**: Every `.param`, `.model`, and component definition must start on a NEW line.
6. **Single noise method**: Use ONLY ONE noise specification (either `onoise_total` for integrated value OR `onoise_spectrum` for frequency response, not both).
7. **Differential check**: Charge pump outputs are typically single-ended (non-differential), so output differential=false unless proven otherwise.
8. **CMFB stability**: Set to false for charge pump circuits (they don't typically use CMFB loops).
9. **Comments**: Remember to add short comments to tell the purpose of each simulation. Example: *current matching 
10. **Format**: If device does not fit the format, change the device name like (I1 net7 net4 VDD VSS INVERTER) should be changed to (X1 net7 net4 VDD VSS INVERTER) because it's a subcircuit. 
    - alter source from DC to trans is NOT allowed. Should define it outsice already
    alter @vla1[pulse] = [ 0 1.2 10n 50p 50p 1n 100n ]
    alter @vlb1[pulse] = [ 0 1.2 10n 50p 50p 1n 100n ]
"""
    
    max_retries = 5
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
            return response.parsed

        except Exception as e:
            error_msg = str(e)
            
            if "503" in error_msg or "ResourceExhausted" in error_msg:
                retry_count += 1
                wait_sec = 30 * retry_count
                print(f"Model busy (503). Retry #{retry_count}. ")
                gen_utils.test_delay(wait_sec)
            elif "429" in error_msg or "TooManyRequests" in error_msg:
                retry_count += 1
                wait_sec = 120 * retry_count
                print(f"Rate limit exceeded (429). Retry #{retry_count}. ")
                gen_utils.test_delay(wait_sec)
            else:
                print(f"An unexpected error occurred: {e}")
                raise e
        
        if retry_count >= max_retries:
            raise RuntimeError("Max retries reached. The model may be unavailable.")

    #out of while True and files exist.
# def measuremnt(spice_result, path, files):




