
from google.adk.agents import LlmAgent
GEMINI_MODEL = "gemini-2.0-flash"

DC_simulate_agent = Agent(
    name="DCsimulateAgent",
    # https://ai.google.dev/gemini-api/docs/models
    model="gemini-2.0-flash",
    description="Analog OPAMP Design DC simulation agent",
    instruction="""
    You are a helpful Analog OPAMP Design DC simulation Agent. 
    
    Based on the lead information

    1. Choose DC voltage sources 
    2. Tell what are the input ports to apply voltage and what is the output port.
    3. What are the voltages applied to input ports 
    4. what are the DC opearting points for 5 most important nodes.

    """,
    #maybe in 1, use current source in the future
    # before_agent_callback=modify_attachment
)