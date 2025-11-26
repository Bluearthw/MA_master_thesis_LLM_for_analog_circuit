from google import genai
from google.genai import types

# import os
from pydantic import BaseModel, Field
######################
# local import
import local_config
import utils
import tools

# initiation
model_used = "gemini-2.0-flash"
model_used_25 = "gemini-2.5-flash"

# cir_num = input()
cir_num = 6
cir_path = f"1genai/data/{cir_num}/{cir_num}.cir"
print("==cir_path\n",cir_path)

circuit_string = utils.get_file_to_str(
    cir_path 
)  # here adding .include also?

######################
# structure output
######################
class NetlistFlow(BaseModel):
    netlist: str = Field(description="The circuit netlist.")


client = genai.Client(api_key=local_config.GOOGLE_API_KEY)

contents = [circuit_string]
circuit_string = utils.clean_netlist(circuit_string)
circuit_string = utils.add_params(circuit_string)
circuit_string = utils.add_DC_source(circuit_string)

print("==cir_str\n",circuit_string)


# region 2nd agent, add C load, with thinking to see whether C is needed
#####################
# contents = [ local_config.netlist_with_load]
# contents = [ local_config.netlist_without_load]
contents = [circuit_string]
tools_available = [
    types.Tool(
        function_declarations=[
            tools.add_C_load_declaration,
            tools.add_OP_simulation_declaration,
        ]
    )
]
config = types.GenerateContentConfig(
    # thinking_config=types.ThinkingConfig(thinking_budget=0),
    system_instruction="""
            You are an experienced analog designer. 
            You are given an incomplete, flawed netlist and tools. Analyze the provided netlist.
            1, If no load is present, you should first add a load capacitor. 
                You must specify the output node. You should respond the final netlist.
            2, If a load is present or just added, add an input DC source and op simulation. You must specify the input node. 
#             You should respond the final netlist.
            """,
    temperature=0,
    tools=tools_available,
)
response = client.models.generate_content(
    model=model_used_25,  # should use 2.5 here, using 2.0 require 1 more step, also thinking is required
    config=config,
    contents=contents,
)
# print("final output",response.text)
tool_call = response.candidates[0].content.parts[0].function_call

# print("==function_call\n", tool_call)
# print("==resonse\n", response.text)

while tool_call:
    if tool_call.name == "add_C_load":
        result = utils.add_C_load(tool_call.args["netlist"], tool_call.args["node"])
    elif tool_call.name == "add_OP_simulation":
        result = utils.add_OP_simulation(tool_call.args["netlist"], tool_call.args["node"])
    function_response_part = types.Part.from_function_response(
        name=tool_call.name,
        response={"result": result},
    )
    print("==result\n", result)
    contents.append(
        response.candidates[0].content
    )  # Append the content from the model's response.
    contents.append(
        types.Content(role="user", parts=[function_response_part])
    )  # Append the function response
    response = client.models.generate_content(
        model=model_used_25,
        config=config,
        contents=contents,
    )
    tool_call = response.candidates[0].content.parts[0].function_call
    print("==function_call\n", tool_call)
circuit_string = ""

for part in response.candidates[0].content.parts:
    if not part.text:
        continue
    else:
        circuit_string += f"\n{part.text}\n"

print("=" * 100)
print(circuit_string)
# endregion

#region op simulation
output = utils.pyspice_op_sim(circuit_string)
#endregion

