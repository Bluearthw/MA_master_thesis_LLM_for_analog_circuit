from google import genai

from genai_agent import local_config
from genai_agent import tools
from utils import gen_utils
def debug_agent_flow(netlist, error_message, cir_num, spec_sims):
    print("==netlist in debug agent\n", netlist)
    print("==error_message\n", error_message)
    client = genai.Client(api_key=local_config.GOOGLE_API_KEY_yong)
    contents = f"""You are an expert Analog IC Designer and NGSpice Specialist.
Your goal is to fix a netlist with error or warning: {netlist} based on the error message: "{error_message}". You are also given a specification id table: {local_config.table_specs_id} and the specification-simulation needed from previous agent:{spec_sims}. 
You should output the fixed netlist and simply the fixing info. Also, if the specification-simulation relationship is not enought or redundant, you should output updated it.
### STRICT FORMATTING RULES:
0, - ONE COMMAND PER LINE: Every '.param', '.model', or component must start on a NEW line. 
   - BAD: .param VDD=1.2 .param W=1u
   - GOOD: 
     .param VDD=1.2
     .param W=1u l=1u m=1
1, - PARAMETER SYNTAX: Use '.param name=value'. Do not use curly brackets {{}} if an '=' is present (e.g., 'dc=VDD' is good, 'dc={{VDD}}' is bad).
But for resistors or capacitors, they need {{}}. 
Example: 
C1 VOUT1 VSS {{C_val}}
R0 net10 tail {{R_val}}

2, - In NGSpice, you can use inoise_total or onoise_total if the integration noise is required. If 
Example for input refer total noise integrated:
noise v(VOUT1) vin dec 10 1 100G
wrdata ./1genai/output/{cir_num}/noise.csv inoise_total

3, - There is only 1 wrdata line after noise simulation But simulation like op can have multiple wrdata.
 -BAD:
    noise v(VOUT1) Vdm dec 10 1 100G
    wrdata ./1genai/output/155/noise_total.csv inoise_total
    wrdata ./1genai/output/155/noise_spectrum.csv inoise_spectrum
    
4, - if there is 'set curplot = noise2'. You can try to remove it. If there is inoise_spectrum or onoise_spectrum with setplot error. Try to use onoise_total or inoise_total first.
5, - Device Format: If device does not fit the format, change the device name like (I1 net7 net4 VDD VSS INVERTER) should be changed to (X1 net7 net4 VDD VSS INVERTER) because it's a subcircuit. 
6, - Source Alteration: alter source from DC to trans is NOT allowed. Should define it outsice already
    alter @vla1[pulse] = [ 0 1.2 10n 50p 50p 1n 100n ]
    alter @vlb1[pulse] = [ 0 1.2 10n 50p 50p 1n 100n ]
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
