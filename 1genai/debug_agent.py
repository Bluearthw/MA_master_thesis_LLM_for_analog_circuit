from google import genai
from google.genai import types

import local_config
import utils
import tools
def debug_agent(netlist, error_message, cir_num):
    print("==netlist in debug agent\n", netlist)
    print("==error_message\n", error_message)
    client = genai.Client(api_key=local_config.GOOGLE_API_KEY_yong)
    contents = f"""You are an expert Analog IC Designer and NGSpice Specialist.
Your goal is to fix a bugged netlist: {netlist} 
based on this error message: "{error_message}".
### STRICT FORMATTING RULES:
0, ONE COMMAND PER LINE: Every '.param', '.model', or component must start on a NEW line. 
   - BAD: .param VDD=1.2 .param W=1u
   - GOOD: 
     .param VDD=1.2
     .param W=1u l=1u m=1
1, PARAMETER SYNTAX: Use '.param name=value'. Do not use curly brackets {{}} if an '=' is present (e.g., 'dc=VDD' is good, 'dc={{VDD}}' is bad).
2, In NGSpice, you can use inoise_total if the integration noise is required. 
Example1 for input refer total noise integrated:
noise v(VOUT1) vin dec 10 1 10G
wrdata ./1genai/output/{cir_num}/noise.csv inoise_total
Example2 :
noise v(VOUT1) vin dec 10 1 10G
wrdata ./1genai/output/{cir_num}/noise.csv inoise_spectrum
3, There is only 1 wrdata line after 1 simulation.
 -BAD:
    noise v(VOUT1) Vdm dec 10 1 100G
    wrdata ./1genai/output/155/noise_total.csv inoise_total
    wrdata ./1genai/output/155/noise_spectrum.csv inoise_spectrum
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
                "response_schema": tools.Struct_debug,
                # "response_json_schema": Struct_flow.model_json_schema(),
            },
            )
            struc = response.parsed
            print("==netlist after debug",struc.netlist)
            # print(str.sims)
            print("==debug agent spec sims", struc.spec_sims)
            print("==debug agent fix info", struc.fix_info)
            return struc
        except Exception as e:
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
