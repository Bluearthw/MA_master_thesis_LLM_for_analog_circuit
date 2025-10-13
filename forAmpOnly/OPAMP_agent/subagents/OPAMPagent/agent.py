
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
    output_key="opamp_info",
    # before_agent_callback=modify_attachment
)