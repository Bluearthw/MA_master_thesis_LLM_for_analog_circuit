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
cir_num = 9
cir_path = f"1genai/data/{cir_num}/{cir_num}.cir"


circuit_string = utils.get_file_to_str(
    cir_path, "**== imcomplete cir file:\n"
)  # here adding .include also?
# ====
# tool use
# ====


# ====
# structure output
# ====
class NetlistFlow(BaseModel):
    netlist: str = Field(description="The circuit netlist.")


client = genai.Client(api_key=local_config.GOOGLE_API_KEY)

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
# print(response.text)
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
md_string = ""
# monitoring the thinking summary and the final answer
for part in response.candidates[0].content.parts:
    if not part.text:
        continue
    if part.thought:
        md_string += f"# Thought Summary\n{part.text}\n"
    else:
        md_string += f"# Answer Text\n{part.text}\n"
        # md_string += "################\n"

print("=" * 100)
print(md_string)

#####################
# 2nd agent, add C load, with thinking to see whether C is needed
# # # ## # # ## # # #

# contents = [ local_config.netlist_with_load]
# contents = [ local_config.netlist_without_load]
contents = [md_string]
# use the tool to 
# Tell the tool the node that load capacitor should connect to besides VSS. 
# Then response the netlist output from the tool.
config = types.GenerateContentConfig(
    # thinking_config=types.ThinkingConfig(thinking_budget=0),
    system_instruction="""
            You are an experienced analog designer. 
            You are given an incomplete, flawed netlist and tools. Analyze the provided netlist.
            1, If no load is present, you must immediately call the tool 'add_load_capacitance'. 
                You must specify the output node.
            2, If a load is present, respond with a short analysis of the circuit.
            You should response the final netlist also.
            """,
    temperature=0,
    tools=tools_available,

)
response = client.models.generate_content(
        model=model_used_25,# should use 2.5 here, using 2.0 require 1 more step, also thinking is required
        config=config,
        contents=contents,
    )
# print("final output",response.text)
tool_call = response.candidates[0].content.parts[0].function_call

print("==function_call\n", tool_call)
print("==resonse\n",response.text)

if tool_call and tool_call.name == "add_C_load":
    result = utils.add_C_load(tool_call.args['netlist'], tool_call.args['node'])
    function_response_part = types.Part.from_function_response(
            name=tool_call.name,
            response={"result": result},
        )
    print("==result\n",result)
    contents.append(response.candidates[0].content) # Append the content from the model's response.
    contents.append(types.Content(role="user", parts=[function_response_part])) # Append the function response
    response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=config,
            contents=contents,
        )
    print("response\n",response)
    tool_call = response.candidates[0].content.parts[0].function_call

if tool_call:
    print("\n??????\n")
else:
    for part in response.candidates[0].content.parts:
        if not part.text:
            continue
        if part.thought:
            md_string += f"# Thought Summary\n{part.text}\n"
        else:
            md_string += f"# Answer Text\n{part.text}\n"

    print("="*100)
    print(md_string)
# md_path = "1genai/data/6/edited_explanation.md"
# md_string = utils.get_file_to_str(md_path, "**==circuit explanation:\n")

# contents = [
#     types.Content(role="user", parts=[types.Part(text=circuit_string + md_string)])
# ]

# client = client = genai.Client(api_key=local_config.GOOGLE_API_KEY)
# response = client.models.generate_content(
#     model=model_used,
#     config=types.GenerateContentConfig(
#         thinking_config=types.ThinkingConfig(thinking_budget=0),  # disable thinking
#         system_instruction="""
#             You are a helpful Analog OPAMP Design Information Agent.
#             You know DC amplifier and AC amplifier.
#             You should understand SPICE netlist (.cir) and circuit explanation (.md) from the user.
#             Format your response as a well-structured report section with:
#             1 Number of ports of the netlist, it can be seen from the .cir file.
#                 Specify the input ports and output ports.
#             2 Number of transistors used.
#             3 The type of the circuit. DC amplifier or AC amplifier.
#             4 Important specifications.
#                 If there are more than 5 specifications, choose the most important 5 specifications.
#             5 The simulation that the circuit should go through.
#                 If there are more than 5 simulations, choose the most important 5 simulations.
#         """,
#         temperature=0,
#     ),
#     contents=contents,
# )

# # print(response.text)
# # print(type(response.candidates[0].content))

# # contents.append(
# #     types.Content(
# #         role="user",
# #         parts=[types.Part(text=response.candidates[0].content.parts[0].text)]
# #     )
# # )

# example_cir_path = "./1genai/data/TwoStage.cir"
# example_cir = utils.get_file_to_str(example_cir_path, "**==example circuit:\n")


# contents.append(response.candidates[0].content)
# contents.append(types.Content(role="user", parts=[types.Part(text=example_cir)]))
# # =======================#
# # ========2nd agent==========#
# # =======================#
# # print("==contents\n\n",contents)

# # class Circuit_parts(BaseModel):
# #     params: str = Field(..., description="param and include part")
# #     cir: str = Field(..., description="circuit description")
# #     simulation: str = Field(..., description="simulation and end")

# # modify the cir
# """
# ======
# Explicitly tell the model not to use the standard names it defaults to,
#  and strictly enforce the custom format.CRITICAL RULE: For transistors,
# use model names 'nmos' and 'pmos'. For all other components, DO NOT use the names 'resistor' or 'capacitor'. Instead
# ======
# """
# config = types.GenerateContentConfig(
#     thinking_config=types.ThinkingConfig(thinking_budget=0),  # disable thinking
#     system_instruction="""
#             You are an experienced Analog OPAMP Design engineer.
#             You are given an imcomplete Spice circuit , an exapmle circuit and some understanding about the circuit.
#             You should first format the incomplete circuit and later add DC and AC source, by learning the format of example circuit.
#             Do not change the path of '.include'. Do not use () to surround the component nodes. Do not save any result from the simulation.
#             Simulations must be in '.control' part.
#             Then, transistors should use model like 'nmos' and 'pmos' due to the library.
#             For all other components, DO NOT use the names 'resistor' or 'capacitor'.
#             For resistors and capacitors, models are not needed. The name starts with letter 'c' is capacitor like cc. rc is resistor. To apply the value, use {}.

#             Comments should have an independant line and are as little as possible.
#             Format your response as a well-structured report section with:
#             1 The Spice netlist with adding ground and DC source and AC source for AC simulation


#         """,
#     # 2 Why you choose these voltage
#     # 3 if you could not response, tell me what you need and what's wrong
#     max_output_tokens=20_000,
#     temperature=0,
# )


# client = utils.get_client()
# modify_circuit_response = client.models.generate_content(
#     model=model_used,
#     config=config,
#     contents=contents,
# )
# print("==modify circuit response\n\n", modify_circuit_response.text)
# utils.check_file_and_overwrite(
#     "./1genai/cir_response.cir", modify_circuit_response.text
# )
# =======================#
# ========3rd agent==========#
# =======================#
# You should also add AC simulation for later simulation usage to the cir file. You should add DC source to the netlist.
# contents = [response.candidates[0].content]
# contents.append(types.Content(role="user", parts=[types.Part(text=example_cir)]))
# contents.append(types.Content(role="user", parts=[types.Part(text=md_string)]))
# config = types.GenerateContentConfig(
#     thinking_config=types.ThinkingConfig(thinking_budget=0),  # disable thinking
#     system_instruction="""
#             You are an experienced Analog OPAMP Design engineer.

#             You are given an imcomplete Spice circuit , an exapmle circuit and some understanding about the circuit.
#             You should first complete the incomplete circuit by learning the example circuit.
#             The transistor should use model like 'nmos' and 'pmos' due to the library.
#             For resistors and capacitors, the name starts with c is capacitor like cc.
#             Comments should have an independant line and are as little as possible.
#             Make sure that '.include' uses / instead of \ since \4 will be recognized as %.
#             Format your response as a well-structured report section with:
#             1 The Spice netlist with adding ground and DC source and AC source for AC simulation


#         """,
#     # 2 Why you choose these voltage
#     # 3 if you could not response, tell me what you need and what's wrong
#     max_output_tokens=20_000,
#     temperature=0,
# )
# client = utils.get_client()

# add_simulation_response = client.models.generate_content(
#     model="gemini-2.0-flash",
#     config=config,
#     contents=contents,
# )
# print("==add source response\n\n", add_simulation_response.text)
