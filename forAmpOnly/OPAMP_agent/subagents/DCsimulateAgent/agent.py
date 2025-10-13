
from google.adk.agents import LlmAgent
GEMINI_MODEL = "gemini-2.0-flash"

DC_simulate_agent = LlmAgent(
    name="DCsimulateAgent",
    # https://ai.google.dev/gemini-api/docs/models
    model="gemini-2.0-flash",
    description="Analog OPAMP Design DC simulation",
    instruction="""
    You are a helpful Analog OPAMP Design DC simulation Agent. 
    
    Based on the previous OPAMP information:{opamp_info}

    1. Choose DC voltage sources 
    2. Tell what are the possible voltages at input and output ports.
    3. Tell the DC opearting points for 5 most important nodes if there are more than 5 nodes. 
        Other wise, tell as much as possible
    4. Tell the DC gain.
    """,
    output_key ="DC_simulate"
    #maybe in 1, use current source in the future
    # before_agent_callback=modify_attachment
)