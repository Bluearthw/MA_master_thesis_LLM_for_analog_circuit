from google import genai

# import os
# import sys

######################
# local import
from genai_agent import local_config
from genai_agent import tools
from genai_agent.workflows import workflow

from utils import gen_utils as gen_utils

path_output = local_config.path_output

def test_make_cir_sim(cir_num, path_output_num, category_str, netlist, has_input, trimmed_spec_table):
    """Wrapper that uses the shared `sim_debug_meas_loop.test_make_cir_sim`.

    This preserves the original signature while delegating behavior to the
    centralized implementation which calls the workflow-local `add_sim_agent`.
    """
    return workflow.generate_netlist(add_sim_agent, cir_num, path_output_num, category_str, netlist, has_input, trimmed_spec_table)
    
def add_sim_agent(netlist, category, cir_num=4, trimmed_spec_table=None, is_diff=None):
    line_wrdata_path_num = "wrdata " + path_output + str(cir_num)
    client = gen_utils.get_client()
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
   - Output: {line_wrdata_path_num}/op_dc_vout.csv v(VOUT1)

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

0. **Circuit requirements**: This is a DC reference. Ensure it has proper biasing network, feedback path, and current generation mechanism.
1. **Differential check**: Bandgap outputs are typically single-ended (non-differential), so output differential=false unless proven otherwise.
2. **CMFB stability**: Set to false for bandgap references (they don't typically use CMFB loops).
{local_config.general_rules.replace('{f_end}', f_end)} 
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
            
            retry_count += 1
            if "503" in error_msg or "ResourceExhausted" in error_msg:
                wait_sec = 30 * retry_count
                print(f"Model busy (503). Retry #{retry_count}. ")
                gen_utils.test_delay(wait_sec)
            elif "429" in error_msg or "TooManyRequests" in error_msg:
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




