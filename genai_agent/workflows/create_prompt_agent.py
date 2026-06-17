from google import genai
import sys

#local import
sys.path.append(".")
from utils import gen_utils
from genai_agent.data import local_config
from genai_agent.data import response_schema
def cmfb_agent(netlist, cir_num=4):
    client = gen_utils.get_client()
    contents = """# Role & Purpose
You are an AI Prompt Engineer and Senior Analog IC Verification Architect. Your job is to take a raw analog circuit category description and compile a precise, production-grade System Prompt for a downstream NGSpice Netlist Generation Agent.

# Task Instructions
1. **Analyze Input**: Read the provided `category_name`, its `raw_category_prose`, and the array of `required_specs`.
2. **Synthesize Simulation Block**: For every item in `required_specs`, use your expert knowledge of electrical engineering to draft an explicit NGSpice test execution case. You must specify:
   - The type of simulation analysis needed (`.ac`, `.dc`, `.tran`, `.op`).
   - The concrete `.control` block formatting syntax using `{line_wrdata_path_num}` for the output file naming convention.
3. **Formulate Topology Rules**: Translate the `raw_category_prose` into structural design guidelines (e.g., how ports should be handled, whether it typically uses Differential Outputs or Common-Mode Feedback (CMFB)).
4. **Enforce Variables**: Ensure the final prompt text naturally contains the placeholders needed by the runtime runner: `{netlist}`, `{cir_num}`, `{trimmed_spec_table}`, `{category_json}`, `{line_wrdata_path_num}`, and `{general_rules}`.

# Output Format
Your response must be a clean, unquoted text block containing the finalized markdown system prompt, ready to be saved into the master prompt database."""

    max_retries = 5
    retry_count = 0
    
    while True:
        try:
            response = client.models.generate_content(
                model=local_config.agent_model,
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema.Struct_cmfb_agent,
                },
            )
            return response.parsed

        except Exception as e:
            error_msg = str(e)
            
            if "503" in error_msg or "ResourceExhausted" in error_msg:
                retry_count += 1
                wait_sec = 60 * retry_count
                print(f"Model busy (503). Retry #{retry_count}.")
                import time
                time.sleep(wait_sec)
            elif "429" in error_msg or "TooManyRequests" in error_msg:
                retry_count += 1
                wait_sec = 60 * retry_count
                print(f"Rate limit exceeded (429). Retry #{retry_count}.")
                import time
                time.sleep(wait_sec)
            else:
                print(f"An unexpected error occurred: {e}")
                raise e
        
        if retry_count >= max_retries:
            raise RuntimeError("Max retries reached. The model may be unavailable.")