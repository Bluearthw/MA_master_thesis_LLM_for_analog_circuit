
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
        And use it for the DC gain calculation as an initial value.
    3. Tell the DC opearting points. If there are more than 5 nodes, choose the most important 5 nodes. 
        
    4. Tell the DC gain. You can assume initial values.
    """,
    output_key ="DC_simulate"
    #maybe in 1, use current source in the future
    # before_agent_callback=modify_attachment
)