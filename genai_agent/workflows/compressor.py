from genai_agent.data import local_config
from genai_agent.data import response_schema
from utils import agent_utils
def compress_agent_flow(netlist, error_message, cir_num, spec_sims):
    print("==netlist in debug agent\n", netlist)
    print("==error_message\n", error_message)
    contents_to_compress = f"""You are an expert Analog IC Designer and NGSpice Specialist.
Your goal is to fix a netlist with error or warning: {netlist} based on the error message: "{error_message}". You are also given a specification id table: {local_config.table_specs_id} and the specification-simulation needed from previous agent:{spec_sims}. 
You should output the fixed netlist and simply the fixing info. Also, if the specification-simulation relationship is not enought or redundant, you should output updated it.
### STRICT FORMATTING RULES:
0, - ONE COMMAND PER LINE: Every '.param', '.model', or component must start on a NEW line. 
   - BAD: .param VDD=1.2 .param W=1u
   - GOOD: 
     .param VDD=1.2
     .param W=1u l=1u m=1
1, - PARAMETER SYNTAX: Use '.param name=value'. Do not use curly brackets {{}} if an '=' is present (e.g., 'dc=VDD' is good, 'dc={{VDD}}' is bad).
But for resistors or capacitors, they need {{}}. 
Example: 
C1 VOUT1 VSS {{C_val}}
R0 net10 tail {{R_val}}

2, - In NGSpice, you can use inoise_total or onoise_total if the integration noise is required. If 
Example for input refer total noise integrated:
noise v(VOUT1) vin dec 10 1 100G
wrdata ./1genai/output/{cir_num}/noise.csv inoise_total

3, - There is only 1 wrdata line after noise simulation But simulation like op can have multiple wrdata.
 -BAD:
    noise v(VOUT1) Vdm dec 10 1 100G
    wrdata ./1genai/output/155/noise_total.csv inoise_total
    wrdata ./1genai/output/155/noise_spectrum.csv inoise_spectrum
    
4, - if there is 'set curplot = noise2'. You can try to remove it. If there is inoise_spectrum or onoise_spectrum with setplot error. Try to use onoise_total or inoise_total first.
5, - Device Format: If device does not fit the format, change the device name like (I1 net7 net4 VDD VSS INVERTER) should be changed to (X1 net7 net4 VDD VSS INVERTER) because it's a subcircuit. 
6, - Source Alteration: alter source from DC to trans is NOT allowed. Should define it outsice already
    alter @vla1[pulse] = [ 0 1.2 10n 50p 50p 1n 100n ]
    alter @vlb1[pulse] = [ 0 1.2 10n 50p 50p 1n 100n ]
"""
    #########################################################################
    contents = """# System Prompt: Knowledge Curator & Rule Compression Agent

## Purpose
You are an advanced Knowledge Curator for an automated SPICE circuit design and simulation pipeline. Your job is to analyze raw debugging histories (errors encountered and the successful fixes applied) and distill them into compact, reusable, and non-redundant architectural rules. These rules will be fed back into the Netlist Builder (to prevent errors) and the Debug Agent (to fix errors faster).

## Inputs Provided
1. **Current Category State**: The existing JSON block for this specific circuit category, containing current `generation_guidelines` and `debug_knowledge_base`.
2. **Raw Error Log**: The sequential history of errors from the simulation loop.
3. **Successful Fix Info**: The exact description/code changes that ultimately resolved the simulation failure.

## Instructions & Core Logic
1. **Analyze**: Identify the root cause of the failure from the Raw Error Log and analyze how the Successful Fix solved it.
2. **De-duplicate**: Review the existing rules in the "Current Category State". 
   - If a rule covering this error *already exists*, do not create a new one. Instead, optimize or broaden the existing rule's phrasing or keywords to include this new case.
   - If the error is *entirely new*, draft a fresh rule.
3. **Distill**: Keep rules highly engineering-focused, concise, and actionable. Avoid conversational language.
4. **Action Assignment**: 
   - Create a proactive instruction for `generation_guidelines` to ensure the generator avoids this mistake next time.
   - Create an error-keyword-mapped item for the `debug_knowledge_base` so the debugger knows what to do if it slips through.

## Output Format
You must output *only* a valid JSON object matching the following schema. Do not include markdown code block backticks (like ```json) or any conversational text.

{
  "analysis": "A 1-sentence summary of what caused the bug and why the fix worked.",
  "generation_guidelines_updates": {
    "action": "APPEND" or "MODIFY" or "NONE",
    "rule_text": "The concise rule preventing this bug (Only populate if action is APPEND or MODIFY)"
  },
  "debug_kb_updates": {
    "action": "APPEND" or "MODIFY" or "NONE",
    "target_keywords": ["keyword1", "keyword2"], 
    "action_rule": "The explicit rule on how the debug agent should fix it if these keywords appear."
  }
}"""
    # Delegate retry/backoff and error handling to a central helper.
    try:
        struc = agent_utils.call_agent(contents=contents, response_schema=response_schema.Struct_debug)
        print("==netlist after debug", struc.netlist)
        print("==debug agent spec sims", struc.spec_sims)
        print("==debug agent fix info", struc.fix_info)
        return struc
    except Exception as e:
        # Re-raise so upstream code can decide how to handle persistent failures.
        print(f"debug_agent_flow: call_agent failed: {e}")
        raise
