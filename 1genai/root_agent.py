# from google import genai
from google.genai import types
# import os
import utils
from pydantic import BaseModel, Field

model_used = "gemini-2.0-flash"
model_used_25 = "gemini-2.5-flash"
cir_path = "1genai/data/6/6.cir"

circuit_string = utils.get_file_to_str(
    cir_path, "" 
)
circuit_string = utils.clean_netlist(circuit_string)
print(circuit_string)
# circuit_string = utils.get_file_to_str(
#     cir_path, "**== imcomplete cir file:\n", '.include "./1genai/data/45nm.sp" \n'
# ) # here adding .include also
# print(circuit_string)


md_path = "1genai/data/6/edited_explanation.md"
md_string = utils.get_file_to_str(md_path, "**==circuit explanation:\n")

contents = [
    types.Content(role="user", parts=[types.Part(text=circuit_string + md_string)])
]

client = utils.get_client()
response = client.models.generate_content(
    model=model_used,
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0),  # disable thinking
        system_instruction="""
            You are a helpful Analog OPAMP Design Information Agent. 
            You know DC amplifier and AC amplifier.
            You should understand SPICE netlist (.cir) and circuit explanation (.md) from the user.
            Format your response as a well-structured report section with:
            1 Number of ports of the netlist, it can be seen from the .cir file. 
                Specify the input ports and output ports.
            2 Number of transistors used.
            3 The type of the circuit. DC amplifier or AC amplifier.
            4 Important specifications. 
                If there are more than 5 specifications, choose the most important 5 specifications. 
            5 The simulation that the circuit should go through. 
                If there are more than 5 simulations, choose the most important 5 simulations.         
        """,
        temperature=0,
    ),
    contents=contents,
)

# print(response.text)
# print(type(response.candidates[0].content))

# contents.append(
#     types.Content(
#         role="user",
#         parts=[types.Part(text=response.candidates[0].content.parts[0].text)]
#     )
# )

example_cir_path = "./1genai/data/TwoStage.cir"
example_cir = utils.get_file_to_str(example_cir_path, "**==example circuit:\n")


contents.append(response.candidates[0].content)
contents.append(types.Content(role="user", parts=[types.Part(text=example_cir)]))
# =======================#
# ========2nd agent==========#
# =======================#
# print("==contents\n\n",contents)

# class Circuit_parts(BaseModel):
#     params: str = Field(..., description="param and include part")
#     cir: str = Field(..., description="circuit description")
#     simulation: str = Field(..., description="simulation and end")

# modify the cir
"""
======
Explicitly tell the model not to use the standard names it defaults to,
 and strictly enforce the custom format.CRITICAL RULE: For transistors,
use model names 'nmos' and 'pmos'. For all other components, DO NOT use the names 'resistor' or 'capacitor'. Instead
======
"""
config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=0),  # disable thinking
    system_instruction="""
            You are an experienced Analog OPAMP Design engineer. 
            You are given an imcomplete Spice circuit , an exapmle circuit and some understanding about the circuit.
            You should first format the incomplete circuit and later add DC and AC source, by learning the format of example circuit.
            Do not change the path of '.include'. Do not use () to surround the component nodes. Do not save any result from the simulation. 
            Simulations must be in '.control' part.
            Then, transistors should use model like 'nmos' and 'pmos' due to the library. 
            For all other components, DO NOT use the names 'resistor' or 'capacitor'. 
            For resistors and capacitors, models are not needed. The name starts with letter 'c' is capacitor like cc. rc is resistor. To apply the value, use {}. 
            
            Comments should have an independant line and are as little as possible.
            Format your response as a well-structured report section with:
            1 The Spice netlist with adding ground and DC source and AC source for AC simulation
           
                     
        """,
    # 2 Why you choose these voltage
    # 3 if you could not response, tell me what you need and what's wrong
    max_output_tokens=20_000,
    temperature=0,
)


client = utils.get_client()
modify_circuit_response = client.models.generate_content(
    model=model_used,
    config=config,
    contents=contents,
)
print("==modify circuit response\n\n", modify_circuit_response.text)
utils.check_file_and_overwrite(
    "./1genai/cir_response.cir", modify_circuit_response.text
)
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
