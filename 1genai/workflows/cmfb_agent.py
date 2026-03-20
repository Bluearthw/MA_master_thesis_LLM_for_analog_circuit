from google import genai

import local_config
import tools
def cmfb_agent(netlist, cir_num=4):
    client = genai.Client(api_key=local_config.GOOGLE_API_KEY_yong)
    contents = f"""You are an expert Analog IC Designer and NGSpice Specialist. You are given a differential output netlist and you need to add a Common-Mode Feedback (CMFB) circuit to stabilize the output common-mode voltage.

**Circuit Information:**
- Circuit Number: {cir_num}
- Original Netlist:
{netlist}

**Specifications Table:**
{local_config.table_specs_id}

**Your Objectives:**
1. Analyze the given netlist and identify the differential output nodes (VOUT1, VOUT2)
2. Add a CMFB circuit that:
   - Senses the common-mode voltage: VCMFB = (VOUT1 + VOUT2)/2
   - Compares it to a reference VCMFB_REF (typically VDD/2)
   - Adjusts a bias current or tail current to maintain VCMFB at the setpoint
3. Choose an appropriate CMFB topology (e.g., voltage follower, telescopic, or high-impedance)
4. Add the CMFB control signal to the main differential pair or current mirror tail
5. Ensure the netlist has proper parameters and can be simulated without errors
6. Add AC and DC simulation commands to verify CMFB operation

**CMFB Simulation Requirements:**
- DC operating point analysis to check voltage levels
- AC analysis to verify frequency response with CMFB
- Transient analysis (optional) to verify settling behavior
- Write simulation results to appropriate output files

**Output File Paths** (use circuit number {cir_num}):
- AC Gain with CMFB: ./1genai/output/{cir_num}/ac_gain_cmfb.csv
- CMFB control signal: ./1genai/output/{cir_num}/cmfb_control.csv (transient)

**Important Rules:**
1. Keep the original differential pair and all component definitions intact
2. Do NOT use bare transistor parameters like w={{}} or l={{}}: use .param instead
   - Example: M_cmfb node1 node2 node3 node4 nmos w=w_cmfb l=l_cmfb m=m_cmfb
3. All passive components (R, C) MUST use {{parameter}} format
4. Add .param statements for all new CMFB circuit components
5. Every netlist command must be on a NEW line (no multi-line statements)
6. The CMFB reference voltage should be a parameter (e.g., VCMFB_REF = VDD/2)
7. Return the complete, augmented netlist ready for simulation
8. Include control block with appropriate simulation commands and output file writes

**Output Format:**
Return the new netlist that is for CMFB.
"""

    max_retries = 5
    retry_count = 0
    
    while True:
        try:
            response = client.models.generate_content(
                model=local_config.agent_model3,
                contents=contents,
                
            )
            return response.text

        except Exception as e:
            error_msg = str(e)
            
            if "503" in error_msg or "ResourceExhausted" in error_msg:
                retry_count += 1
                wait_sec = 60 * retry_count
                print(f"Model busy (503). Retry #{retry_count}.")
                import time
                time.sleep(wait_sec)
            elif "429" in error_msg or "TooManyRequests" in error_msg:
                retry_count += 1
                wait_sec = 120 * retry_count
                print(f"Rate limit exceeded (429). Retry #{retry_count}.")
                import time
                time.sleep(wait_sec)
            else:
                print(f"An unexpected error occurred: {e}")
                raise e
        
        if retry_count >= max_retries:
            raise RuntimeError("Max retries reached. The model may be unavailable.")