from google import genai
import sys
#local import
sys.path.append("./1genai")
import local_config
import tools
def cmfb_agent(netlist, cir_num=4):
    client = genai.Client(api_key=local_config.GOOGLE_API_KEY_yong)
    contents = f"""You are an expert Analog IC Designer and NGSpice Specialist. 
    You are given a differential output netlist and you need to modify the netlist and try to add simulation to measure the Common-mode feedback (CMFB) for later agent to stabilize the output common-mode voltage.

**Circuit Information:**
- Description: The netlist is already used for other specifications and the simulations are removed. You should add only simulation related to CMFB
- Circuit Number: {cir_num}
- Original Netlist:
{netlist}

You can use Middlebrook Method or any other method that is good. Measurement will be done by following agent using the wrdata output data so meas is not needed.

**Important Rules:**
1. Keep the original differential pair and all component definitions intact
2. Do NOT use bare transistor parameters like w={{}} or l={{}}: use .param instead
   - Example: M0 node1 node2 node3 node4 nmos w=w0 l=l0 m=m0
3. All passive components (R, C) MUST use {{parameter}} format
4. Every netlist command must be on a NEW line (no multi-line statements)
5. The CMFB reference voltage should be a parameter (e.g., VCMFB_REF = VDD/2)
6. Return the complete, augmented netlist ready for simulation
7. Include control block with appropriate simulation commands and output file writes
Example:
ac dec 50 1 100G
wrdata ./1genai/output/{cir_num}/cmfb_stb.csv v(net29)/v(gate_fb)

**Output Format:**
Return the new netlist that is for CMFB. The specification (CMFB stb), id (20) and the output file path. 
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
                    "response_schema": tools.Struct_cmfb_agent,
                },
            )
            return response.parsed

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
                wait_sec = 60 * retry_count
                print(f"Rate limit exceeded (429). Retry #{retry_count}.")
                import time
                time.sleep(wait_sec)
            else:
                print(f"An unexpected error occurred: {e}")
                raise e
        
        if retry_count >= max_retries:
            raise RuntimeError("Max retries reached. The model may be unavailable.")