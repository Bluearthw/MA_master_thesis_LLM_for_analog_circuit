from google import genai
from google.genai import types

import local_config

import tools
def debug_agent(netlist, error_message):
    print("==netlist in debug agent\n", netlist)
    print("==error_message\n", error_message)
    client = genai.Client(api_key=local_config.GOOGLE_API_KEY)
    contents = f"""You are an experienced amplifier designer. You are given a bugged netlist : {netlist}, and an error message from simulation : {error_message}.
Fix the netlist based on the error message so that it can be simulated well. 
Besides general check, there are some typical mistakes:
0, the output netlist is not line by line. e.g., 
.param VDD=1.2 .param w1=0.5u l1=90n m1=1
But it should be:
.param VDD=1.2
.param w1=0.5u l1=90n m1=1
1, dc = {{variable}}. Normally, brackets are not needed if there is =.
2, in noise simulation, vectors are not found. In NGSpice, the noise command produces two separate plots: 'noise1' for spectral density and 'noise2' for integrated noise. So, 'noise1.onoise_spectrum' or 'noise1.inoise_spectrum' (input equivalent noise)   can be tried.  """
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