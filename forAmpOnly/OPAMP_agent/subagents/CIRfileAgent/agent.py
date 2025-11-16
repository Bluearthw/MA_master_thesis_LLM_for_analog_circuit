
from google.adk.agents import LlmAgent
GEMINI_MODEL = "gemini-2.0-flash"

CIR_file_agent = LlmAgent(
    name="CIRfileAgent",
    # https://ai.google.dev/gemini-api/docs/models
    model="gemini-2.0-flash",
    description="Make Analog OPAMP Design CIR",
    instruction="""
    You are a helpful .cir file Agent for ngspice . 
    
    Based on the previous OPAMP information:{opamp_info}, 
    the example .cir file with simulation (cir_example), 
    the input .cir file without simulation (cir_target) 
    and DC infomation {DC_simulate}

    Response with a .cir script with simulation from cir_target,   
    using the language from the cir_example file.
    Make sure that it is like the component name and nodes connected.
    If it is not passive component, add model used and possible defiinition like : m1 2 1 4 5 mmod w=10um or M0 VDD VDD VOUT1 VSS nmosm w=10um
    Do not use brackets like : M0 (1 1 2 0) nmosm. This will raise error in the simulator.
    Do not short the circuit like : VSS 0 0 .
    Do only DC analysis. Maybe Transient also.
    The circuit should be the same as the cir_target. 
    This output .cir file will be fed to next agent to add .model part.
    """,
    output_key ="CIR_file_without_model"
    #maybe in 1, use current source in the future
    # before_agent_callback=modify_attachment
)