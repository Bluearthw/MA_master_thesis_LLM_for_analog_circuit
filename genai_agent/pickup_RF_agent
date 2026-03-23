from pydantic import BaseModel, Field
from google.genai import types

# local import#
import utils
import local_config
client = utils.get_client()

nums = local_config.num_SISO_RF_before_filtered
class IsRF(BaseModel):
    isRF: bool = Field(description="A boolean to see whether the circuit is RF types or not")
for num in nums:
    path_exaplain = local_config.dataset_path +f"/{num}/edited_explanation.md"
    str_explain = utils.get_file_to_lines(path_exaplain,20)# almost half of the explain,
    contents = [str_explain]
    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0),
        system_instruction="""
                You are an experienced and helpful analog designer. 
                You are given a explanation text about a amplifier circuit. 
                Based on it, tell whether the circuit has to be treated as RF circuit or not.
                """,
        temperature=0,
        response_mime_type="application/json",
        response_json_schema=IsRF.model_json_schema(),
    )
    response = client.models.generate_content(
        model=local_config.model_used,  # should use 2.5 here, using 2.0 require 1 more step, also thinking is required
        config=config,
        contents=contents,
    )
    isRF = IsRF.model_validate_json(response.text)
    print("==isRF",isRF)
    print("==num",num)
    if num > 100:
        break
    