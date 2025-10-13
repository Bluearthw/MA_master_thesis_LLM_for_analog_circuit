
from google.adk.agents import LlmAgent

# constant
GEMINI_MODEL = "gemini-2.0-flash"

# agent
opamp_info_agent = LlmAgent(
    name="OPAMPagent",
    # https://ai.google.dev/gemini-api/docs/models
    model="gemini-2.0-flash",
    description="get analog OPAMP Design Information",
    instruction="""
    You are a helpful Analog OPAMP Design Information Agent. 
    
    You should understand SPICE netlist (.cir) and circuit explanation (.md) from the user.
    example output:
    1 Format your response as a well-structured report section with:
    2 Number of ports of the netlist, it can be seen from the .cir. Specify the input ports [in] and output ports with [out]
    3 Number of transistors used
    4 The type of the circuit
    5 The specifications that are important
    6 The simulation that the circuit should go through

    """,
    output_key="opamp_info",
    # before_agent_callback=modify_attachment
)