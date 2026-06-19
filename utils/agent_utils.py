import os
import sys
import json

import time
import traceback
from google import genai
from google.genai.types import HttpOptions
sys.path.append('.')
##local import
from utils import gen_utils
from genai_agent.data import local_config
from utils import file_utils
def get_client():
    return genai.Client(http_options=HttpOptions(api_version="v1"))


def call_agent(contents: str,
               response_schema,
               model: str = None,
               max_retries: int = 5,
               backoff_base: int = 60,
               client=None,
               config_extra: dict = None):
    """Call the model and return parsed response with retry/backoff for transient errors.

    Args:
        contents: prompt string to send to the model.
        response_schema: response schema object (e.g., tools.Struct_debug).
        model: model id to use. If None, uses `local_config.agent_model`.
        max_retries: maximum retry attempts for transient failures.
        backoff_base: base wait seconds used for exponential backoff (wait = backoff_base * attempt).
        client: optional pre-created client. If None, `gen_utils.get_client()` is used.
        config_extra: additional key/value pairs to include in the `config` passed to `generate_content`.

    Returns:
        response.parsed object on success.

    Raises:
        RuntimeError when max retries are exceeded or for non-transient errors.
    """
    if model is None:
        model = local_config.agent_model

    if client is None:
        client = get_client()

    attempt = 0
    while True:
        try:
            cfg = {
                "response_mime_type": "application/json",
                "response_schema": response_schema,
            }
            if config_extra:
                cfg.update(config_extra)

            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=cfg,
            )
            return response.parsed

        except Exception as e:
            err = str(e)
            # Transient conditions we want to retry
            transient = False
            if any(x in err for x in ("503", "ResourceExhausted", "TooManyRequests", "429")):
                transient = True

            attempt += 1
            if transient and attempt <= max_retries:
                wait_sec = backoff_base * attempt
                print(f"Model busy (transient). Retry #{attempt} in {wait_sec}s")
                try:
                    gen_utils.test_delay(wait_sec)
                except Exception:
                    time.sleep(wait_sec)
                continue

            # If not transient or exceeded retries, re-raise with context
            tb = traceback.format_exc()
            raise RuntimeError(f"call_agent failed after {attempt} attempts: {err}\n{tb}") from e


def update_master_registry(category_num, agent_output_str):
    # Load the agent's structured suggestion
    update_data = json.loads(agent_output_str)
    
    # Load your existing master JSON
    master_kb = file_utils.get_dict_from_json('categories.json')
    cat_entry = master_kb["categories"][str(category_num)]
    
    # 1. Handle Generation Guidelines Update
    g_update = update_data["generation_guidelines_updates"]
    if g_update["action"] == "APPEND":
        cat_entry["generation_guidelines"].append(g_update["rule_text"])
    elif g_update["action"] == "MODIFY":
        # Logic to replace or optimize an existing rule string
        pass

    # 2. Handle Debug Knowledge Base Update
    d_update = update_data["debug_kb_updates"]
    if d_update["action"] == "APPEND":
        new_entry = {
            "error_keywords": d_update["target_keywords"],
            "action_rule": d_update["action_rule"]
        }
        cat_entry["debug_knowledge_base"].append(new_entry)
        
    # Save the updated "brain" back to disk
    file_utils.save_dict_to_json(master_kb, 'categories.json')
    print(f"Successfully compressed and integrated knowledge for category {category_num}!")

def get_workflow_prompts_json():
    prompts_path = local_config.path_prompts + "workflow_prompts.json"
    dict = file_utils.get_dict_from_json(prompts_path)
    
    return dict
def save_workflow_prompts_json(prompt_dict, cat_key):
    # 1. Define the pristine structure for the new circuit category
    category_rules = {
        "generation_guidelines": [],
        "debug_knowledge_base": {}
    }
    # 2. CRITICAL: Commit this placeholder back into the master prompt dictionary
    prompt_dict[cat_key] = category_rules
    prompts_path = local_config.path_prompts + "workflow_prompts.json"
    file_utils.save_dict_to_json(prompt_dict, prompts_path)
    return category_rules

def prepare_workflow_prompts_json(category_num):
    prompt_dict = get_workflow_prompts_json()# should update for every circuit, in the future, some flag to control
    general_rules = "\n".join(prompt_dict.get('general_rules', []))# list
    cat_key = f'category_{category_num}'
    category_rules = prompt_dict.get(cat_key)# dict? obj?
    if category_rules is None:
        category_rules = save_workflow_prompts_json(prompt_dict, cat_key)
    category_gen_rules = "\n".join(category_rules.get('generation_guidelines', []))# list
    category_debug_rules = "\n".join(category_rules.get('debug_knowledge_base', []))# list
    cat_prompt_path = local_config.path_prompts + f"prompt_{category_num}.md"
    is_cat_propmt_exist = os.path.isfile(cat_prompt_path)
    return general_rules, category_gen_rules, category_debug_rules, is_cat_propmt_exist, cat_prompt_path

def check_current_simulation(spec_sims):
    for spec_sim in spec_sims:
        if spec_sim.spec_id == 22:#current is there:
            return True
    return False

def update_spec_json(spec_dict, new_spec_list, spec_table_path: str | None = None):
    """Add new specification names to the spec-id mapping.

    - `spec_dict` may have integer or string keys representing spec ids.
    - `new_spec_list` is an iterable of spec name strings to add.
    - If `spec_table_path` is provided, the updated table is saved to that path
      with stringified keys (JSON-compatible).

    Returns the updated spec_dict (with integer keys).
    """
    # Normalize keys to ints and find current max id
    try:
        existing_ids = [int(k) for k in spec_dict.keys()]
    except Exception:
        # Fallback: if keys are already ints or something odd, coerce conservatively
        existing_ids = [k for k in spec_dict.keys() if isinstance(k, int)]

    max_id = max(existing_ids) if existing_ids else -1

    # Build a set of existing spec names to avoid duplicates
    existing_names = set(spec_dict.values())

    # Add each new spec if not already present
    for spec_name in (new_spec_list or []):
        if spec_name in existing_names:
            continue
        max_id += 1
        spec_dict[max_id] = spec_name
        existing_names.add(spec_name)

    # Optionally persist to disk (use string keys for JSON)
    if spec_table_path:
        jsonable = {str(k): v for k, v in spec_dict.items()}# though json.dumps transform also
        file_utils.save_dict_to_json(jsonable, spec_table_path)

    return spec_dict