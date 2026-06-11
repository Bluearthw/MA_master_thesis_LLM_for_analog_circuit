import time
import traceback
from google import genai
from google.genai.types import HttpOptions
##local import
from utils import gen_utils
from genai_agent.data import local_config

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

import json

def update_master_registry(category_num, agent_output_str):
    # Load the agent's structured suggestion
    update_data = json.loads(agent_output_str)
    
    # Load your existing master JSON
    master_kb = gen_utils.load_json_to_dict('categories.json')
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
    gen_utils.save_dict_to_json(master_kb, 'categories.json')
    print(f"Successfully compressed and integrated knowledge for category {category_num}!")