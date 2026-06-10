from google import genai
import sys
# import os
# import sys

######################
# local import
from genai_agent import local_config
import os
from genai_agent import tools
from genai_agent.workflows import workflow
from utils import gen_utils as gen_utils

path_output = local_config.path_output

def netlist_builder(netlist, category, category_num, cir_num=4, trimmed_spec_table=None, is_diff=False):
    line_wrdata_path_num = "wrdata " + path_output + str(cir_num)
    
    client = gen_utils.get_client()
    f_end= "1T"
    general_rules = local_config.general_rules.replace('{f_end}', f_end)

    prompt_path = os.path.join(local_config.path_prompts, f"prompt_{category_num}.md")
    contents = gen_utils.get_file_to_str(prompt_path).format(general_rules=general_rules,
                                                           f_end=f_end, 
                                                           line_wrdata_path_num=line_wrdata_path_num, 
                                                           netlist=netlist,
                                                           is_diff = is_diff,
                                                           trimmed_spec_table = trimmed_spec_table,
                                                           category = category,
                                                           cir_num = cir_num
                                                           )

    max_retries = 5  # Optional: prevent infinite loops if the server is truly down
    retry_count = 0
    
    while True:
        try:
            response = client.models.generate_content(
                model=local_config.agent_model,
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": tools.Struct_flow,
                },
            )
            # If successful, return the parsed data
            return response.parsed

        except Exception as e:
            # Check if the error is a 503 (Service Unavailable)
            # Note: Depending on your library version, 'e' might have a .code or .status_code
            error_msg = str(e)
            
            retry_count += 1
            if "503" in error_msg or "ResourceExhausted" in error_msg:
                wait_sec = 40*retry_count  # Exponential backoff: 60s, 120s, 180s, etc.
                print(f"Model busy (503). Retry #{retry_count}. ")
                gen_utils.test_delay(wait_sec)  # Wait before retrying
            elif "429" in error_msg or "TooManyRequests" in error_msg:
                wait_sec = 120*retry_count  # Exponential backoff: 60s, 120s, 180s, etc.
                print(f"Rate limit exceeded (429). Retry #{retry_count}. ")
                gen_utils.test_delay(wait_sec)  # Wait before retrying
            else:
                # If it's a different error (like a syntax error in your code), 
                # we want to see it immediately rather than looping.
                print(f"An unexpected error occurred: {e}")
                raise e
        if retry_count >= max_retries:
            raise RuntimeError("Max retries reached. The model may be unavailable.")



