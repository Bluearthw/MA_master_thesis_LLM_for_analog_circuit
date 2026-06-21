from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict
class Struct_specs_sim(BaseModel):
    spec: str = Field(description="The name of the specification e.g., 'gain', 'bandwidth'. Different specs may require same simulation. e.g., gain and bandwidth both require ac simulation. Some specs may require multiple simulation files. e.g. current matching requires both source_current and sink_current")
    # sim_name: str = Field(description="corresponding simulation name. Different specs may require same simulation. e.g., gain and bandwidth both require ac simulation.")
    sim_file_name : str =Field(description="corresponding name of simulations output files. Here are .csv files in the wrdata lines from the generated SPICE netlist. Example: ac_gain.csv")
    spec_id: int = Field(description="Specification ID. There is a table about it. Example: 0=DC Gain. ")

class Struct_flow(BaseModel):
    netlist: str = Field(description="The SPICE netlist. Use standard newlines (\\n) between every line.")
    spec_sims : list[Struct_specs_sim] = Field(description="specifications required and simulations needed. Some specs may require multiple simulation files.")
    is_diff: bool = Field(description="If the circuit is differential output, this field is True.")
    is_CMFB: bool = Field(description="If the circuit has CMFB, this field is True.")
    target_dc_vout: float = Field(description="Define a target DC output voltage based on the circuit.")

class Struct_debug(BaseModel):
    # 1. Force the model to reason FIRST
    bug_analysis: str = Field(description="A clear analysis of the SPICE error message. Explain exactly why the current netlist failed.")
    fix_plan: str = Field(description="A step-by-step technical plan of what parameters, nodes, or models need to be modified to resolve the bug. Be concise"    )
    # 2. Output the payload SECOND
    netlist: str = Field(description="The complete, corrected SPICE netlist incorporating the fix plan. Use standard newlines (\\n)."    )
    spec_sims: List[Struct_specs_sim] = Field(description="The list of simulations needed and why"    )
    fix_info: str = Field(description="A concise summary of the final changes made. This will be archived into the permanent knowledge base."    )

class NewSpecificationItem(BaseModel):
    target_id: str = Field(
        description="The standardized string ID name for the spec (snake_case, e.g., 'slew_rate')."
    )
    human_name: str = Field(
        description="A clean, title-cased, human-readable name for the specification (e.g., 'Slew Rate')."
    )
    aliases: List[str] = Field(
        description="A list of lowercase text aliases that engineers might use to refer to this spec."
    )
    default_value: float = Field(
        description="A mathematically reasonable default float value for this specification type in calculations."
    )
    should_minimize: bool = Field(
        description="Set to True if this metric should be minimized (like noise, settling time). Set to False if it should be maximized (like gain, bandwidth)."
    )

class Struct_Update_Tables(BaseModel):
    new_specifications: List[NewSpecificationItem] = Field(
        description="A structured list containing all newly discovered specifications to append to the system databases."
    )
class Struct_prepare_new_type(BaseModel):
    prompt: str = Field(description="The prompt for the netlist generation agent.")
    missing_specifications_to_add: List[str] = Field(
        description="List of raw specification names found in the requirement but missing from the spec_id_table. They can be simulated in NGspice."
    )
    impossible_specifications: List[str] = Field(description="List of specifications that cannot be simulated in NGspice.")

class GenerationGuidelinesUpdates(BaseModel):
        action: Literal["APPEND", "MODIFY", "NONE"] = Field(description="Action to take on the generation guidelines.")
        rule_text: Optional[str] = Field(default=None, description="Concise rule text to append or use for modification. Populated only when action is APPEND or MODIFY.")

class DebugKbUpdates(BaseModel):
    action: Literal["APPEND", "MODIFY", "NONE"] = Field(description="Action to take on the debug knowledge base.")
    target_keywords: Optional[List[str]] = Field(default=None, description="List of keywords that identify this bug pattern. Populated when action is APPEND or MODIFY.")
    action_rule: Optional[str] = Field(default=None, description="Explicit rule describing how the debug agent should fix issues when those keywords appear.")

class Struct_compress(BaseModel):
    """Compression agent response schema.

    Fields:
      - analysis: one-sentence summary of cause and fix
      - generation_guidelines_updates: instruction whether to append/modify/none
      - debug_kb_updates: instruction whether to append/modify/none plus keywords and rule
    """
    analysis: str = Field(description="A 1-sentence summary of what caused the bug and why the fix worked.")

    
    generation_guidelines_updates: GenerationGuidelinesUpdates = Field(description="Updates for generation guidelines: action and optional rule text.")
    debug_kb_updates: DebugKbUpdates = Field(description="Updates for the debug knowledge base: action, keywords, and action rule.")

