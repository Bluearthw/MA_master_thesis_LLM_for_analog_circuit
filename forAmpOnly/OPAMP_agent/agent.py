from google.adk.agents import SequentialAgent

from .subagents.OPAMPagent import opamp_info_agent
from .subagents.DCsimulateAgent import DC_simulate_agent

# Create the sequential agent with minimal callback
root_agent = SequentialAgent(
    name="LeadQualificationPipeline",
    sub_agents=[opamp_info_agent, DC_simulate_agent],
    description="A pipeline that validates, scores, and recommends actions for sales leads",
)

