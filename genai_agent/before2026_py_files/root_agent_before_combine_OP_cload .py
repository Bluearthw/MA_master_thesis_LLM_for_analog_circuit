from google import genai
from google.genai import types

# import os
from pydantic import BaseModel, Field
import local_config

# local import
import utils
import tools

# initiation
model_used = "gemini-2.0-flash"
model_used_25 = "gemini-2.5-flash"
cir_num = input()
cir_path = f"1genai/data/{cir_num}/{cir_num}.cir"


circuit_string = utils.get_file_to_str(
    cir_path, "**== imcomplete cir file:\n"
)  # here adding .include also?
# ====
# ====


# ====
# structure output
# ====
class NetlistFlow(BaseModel):
    netlist: str = Field(description="The circuit netlist.")


client = genai.Client(api_key=local_config.GOOGLE_API_KEY_yong)

contents = [circuit_string]


contents = [circuit_string]

tools_available = [
    types.Tool(
        function_declarations=[
            tools.clean_netlist_declaration,
            tools.add_params_declaration,
            tools.add_DC_source_declaration,
            tools.add_C_load_declaration,
        ]
    )
]
#####################
# region 1st agent, dealing the circuit
#####################
config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=0),
    system_instruction="""
            You are an experienced analog designer. 
            You are given an incomplete, flawed netlist and tools.
            You should 
            1, clean its format using the tool. 
            2, add some paramters using the tool.
            3, add DC source and GND.
            You should response the final netlist.
        """,
    temperature=0,
    tools=tools_available,
    # response_mime_type= "application/json",
    # response_json_schema = NetlistFlow.model_json_schema(),
)

response = client.models.generate_content(
    model=model_used, contents=contents, config=config
)
# text = response.candidates[0].text
# circuit =NetlistFlow.model_validate_json(response.text)
# print(circuit)
response = client.models.generate_content(
    model=model_used, contents=contents, config=config
)
# text = response.candidates[0].text
# circuit =NetlistFlow.model_validate_json(response.text)
# print(circuit)
# print(response.text)
# print(response.candidates[0].content.parts)
# print(response.candidates[0].content.parts)
# print("function_call", response.candidates[0].content.parts[0].function_call)
tool_call = response.candidates[0].content.parts[0].function_call
while tool_call:
    if tool_call.name == "clean_netlist":
        result = utils.clean_netlist(**tool_call.args)
    elif tool_call.name == "add_params":
        result = utils.add_params(tool_call.args["netlist"])
    elif tool_call.name == "add_DC_source":
        result = utils.add_DC_source(tool_call.args["netlist"])
    # elif tool_call.name == "add_C_load":
    #     result = utils.add_C_load(tool_call.args["netlist"],tool_call.args["node"])
tool_call = response.candidates[0].content.parts[0].function_call
while tool_call:
    if tool_call.name == "clean_netlist":
        result = utils.clean_netlist(**tool_call.args)
    elif tool_call.name == "add_params":
        result = utils.add_params(tool_call.args["netlist"])
    elif tool_call.name == "add_DC_source":
        result = utils.add_DC_source(tool_call.args["netlist"])
    # elif tool_call.name == "add_C_load":
    #     result = utils.add_C_load(tool_call.args["netlist"],tool_call.args["node"])

    function_response_part = types.Part.from_function_response(
        name=tool_call.name,
        response={"result": result},
    )
    function_response_part = types.Part.from_function_response(
        name=tool_call.name,
        response={"result": result},
    )

    # print("==response content", response.candidates[0].content)
    # print("==response result", result)
    contents.append(
        response.candidates[0].content
    )  # Append the content from the model's response.
    contents.append(
        types.Content(role="user", parts=[function_response_part])
    )  # Append the function response
    # client = genai.Client(api_key=local_config.GOOGLE_API_KEY) #maybe removed
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=config,
        contents=contents,
    )
    tool_call = response.candidates[0].content.parts[0].function_call
    print("tool_call", tool_call)
netlist_before_C_load_check = ""
# monitoring the thinking summary and the final answer
for part in response.candidates[0].content.parts:
    if not part.text:
        continue
    if part.thought:
        netlist_before_C_load_check += f"# Thought Summary\n{part.text}\n"
    else:
        netlist_before_C_load_check += f"# Answer Text\n{part.text}\n"

# print("=" * 100)
# print(response_string)
# endregion
#####################
# region 2nd agent, add C load, with thinking to see whether C is needed
#####################
# contents = [ local_config.netlist_with_load]
# contents = [ local_config.netlist_without_load]
contents = [netlist_before_C_load_check]

config = types.GenerateContentConfig(
    # thinking_config=types.ThinkingConfig(thinking_budget=0),
    # thinking_config=types.ThinkingConfig(thinking_budget=0),
    system_instruction="""
            You are an experienced analog designer. 
            You are given an incomplete, flawed netlist and tools. Analyze the provided netlist.
            1, If no load is present, you should add a load capacitor. 
                You must specify the output node. You should response the final netlist.
            2, If a load is present, respond with a short analysis of the circuit.
            3, Add a DC input source and OP simulation. You should specify the input node. 
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

print("==function_call\n", tool_call)
print("==resonse\n", response.text)

is_added_Cload = False
if tool_call and tool_call.name == "add_C_load":
    result = utils.add_C_load(tool_call.args["netlist"], tool_call.args["node"])
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
        model="gemini-2.5-flash",
        config=config,
        contents=contents,
    )
    print("response\n", response)
    tool_call = response.candidates[0].content.parts[0].function_call
response_string = ""
if tool_call:
    print("\n??????\n")
else:
    if is_added_Cload:  # after using tool
        for part in response.candidates[0].content.parts:
            if not part.text:
                continue
            if part.thought:
                response_string += f"# Thought Summary\n{part.text}\n"
            else:
                response_string += f"# Answer Text\n{part.text}\n"

    else:
        response_string = netlist_before_C_load_check

# endregion
print("=" * 100)
print(response_string)

#####################
# region 3rd agent, add DC simulation and input
#####################
config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=0),
    system_instruction="""
            You are an experienced analog designer. 
            You are given an incomplete netlist and tools.
            You should 
            1, clean its format using the tool. 
            2, add some paramters using the tool.
            3, add DC source and GND.
            You should response the final netlist.
        """,
    temperature=0,
    tools=tools_available,
    # response_mime_type= "application/json",
    # response_json_schema = NetlistFlow.model_json_schema(),
)
response = client.models.generate_content(
    model=model_used, contents=contents, config=config
)
# endregion
