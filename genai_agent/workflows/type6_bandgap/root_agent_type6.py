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
    print(target_dc_vout)
    results_original, struct_path_id = sim_debug_meas_loop.sim_debug_measure_loop(netlist, spec_sims, cir_num, path_output_num, is_differential_output, target_dc_vout, has_input, is_CMFB)
    
    combined_results = {'original': results_original}
    path_netlist = path_output_num + "final_netlist.cir"
    gen_utils.save_str_to_file(netlist, path_netlist)
    
    
    
    data_for_dut_yaml = (is_differential_output, has_input, target_dc_vout)

    print("Combined measurement results:", combined_results)
    return combined_results, struct_path_id, path_netlist, spec_sims, data_for_dut_yaml
    
def add_sim_agent(netlist, category, cir_num=4, trimmed_spec_table=None):
    line_wrdata_path_num = "wrdata " + path_output + str(cir_num)
    client = genai.Client(api_key=local_config.GOOGLE_API_KEY_yong)
    f_end = "1T"
    contents = f"""You are an expert Analog IC Designer and NGSpice Specialist. You are given an incomplete netlist for a Bandgap Reference circuit: {netlist}, circuit number {cir_num}, a table of specifications and their IDs: {trimmed_spec_table}, and detailed requirements: {category}.
Your goal is to complete the simulation setup for a DC voltage reference (bandgap) circuit. The netlist must be fully simulated without errors. You should output:
1. The complete, ready-to-run netlist
2. Whether the output is differential (true/false)
3. A list of required specifications and corresponding simulation file paths for measurement
4. Whether CMFB stability check is needed (typically false for bandgap references)

### Bandgap-Specific Rules and Measurements:
**Simulation Examples**:
1. **DC Output Voltage**: Initial operating point to determine nominal VREF
   - Simulation: op
   - Output: {line_wrdata_path_num}/dc_vref.csv v(VOUT1)

2. **Line Regulation**: DC sweep of VDD to measure supply sensitivity (ΔVout/ΔVdd). 
    Example: For a 1.2 V process targeting a 0.6 V reference, a safe nominal sweep is 1.0 V to 1.4 V .
   - Simulation: dc vdd 1.0 1.4 0.01
   - Output: {line_wrdata_path_num}/dc_line_reg.csv v(VOUT1)

3. **Load Regulation**: DC sweep of load current to measure output impedance (ΔVout/ΔIload)
   - Add a variable current load at output (e.g., Iload VOUT1 VSS pulse or dc sweep). 100u is just an example. You can choose the value based on the circuit
   - Simulation: dc Iload 0 100u 1u
   - Output: {line_wrdata_path_num}/dc_load_reg.csv v(VOUT1)

4. **Temperature Coefficient (TC)**: DC sweep of temperature to measure drift (ppm/°C)
   - Simulation: dc temp -40 125 5
   - Output: {line_wrdata_path_num}/dc_temp_coeff.csv v(VOUT1)

5. **Power Supply Rejection Ratio (PSRR)**: AC analysis on supply rail. If there is no AC simulation about the normal gain, take vout
   - Superimpose small AC signal on VDD: Vdd VDD 0 dc=1.2 ac=0.01
   - Simulation: ac dec 10 1 {f_end}
   - Output: {line_wrdata_path_num}/ac_psrr.csv v(VOUT1)

6. **Startup Behavior**: Transient analysis with VDD ramp to ensure proper initialization
   - Use VDD ramp: Vdd VDD 0 PWL(0 0 10u 1.2) which can be combined with other VDD setup. DO NOT use alter vdd pulse(0 1.2 0 10u) in .control part.
   
   - Simulation: tran 50n 100u
   - Output: {line_wrdata_path_num}/tran_startup.csv v(VOUT1)

7. **Output Noise**: Noise analysis for integrated output noise. DO NOT use 'set curplot = noise2' or 'onoise_spectrum'.
   - Simulation: noise v(VOUT1) Vdd dec 10 1 {f_end}
   - Output: {line_wrdata_path_num}/noise.csv onoise_total

8. **Current Consumption**: DC operating current from supply
   - Simulation: op
   - Output: {line_wrdata_path_num}/op_current.csv i(vdd)

### General Netlist Rules:

0. **Load**: Add load capacitance if not present (e.g., Cload=10p at output)
1. **Transistor parameters**: Use `.param` variables without curly brackets on the component line. WRONG: `w={{}}` CORRECT: `w=wp1` with `.param wp1=1u`
2. **Passive components**: Capacitors and resistors MUST use curly brackets with variables. CORRECT: `R0 node1 node2 {{r0}}` with `.param r0=1k`
3. **Circuit requirements**: This is a self-biasing DC reference. Ensure it has proper biasing network, feedback path, and current generation mechanism.
4. **Data output format**: Each measurement must write to a unique CSV file with the circuit number in path! Lines MUST be kept : 'set units=degrees' and 'set wr_vecnames'!
5. **ONE command per line**: Every `.param`, `.model`, and component definition must start on a NEW line.
6. **Differential check**: Bandgap outputs are typically single-ended (non-differential), so output differential=false unless proven otherwise.
7. **CMFB stability**: Set to false for bandgap references (they don't typically use CMFB loops).


"""
    
    max_retries = 5
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




