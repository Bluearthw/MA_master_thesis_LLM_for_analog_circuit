import os
import sys
import json
import re

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
        if spec_sim.spec_num_id == 22:#current is there:
            return True
    return False


def update_tables(struc, specifications_table, spec_tables_path, valid_contracts):
    """Update the unified specifications table database.

    Accepts a Struct_Update_Tables object containing a list of `new_specifications`
    (each with `target_id`, `spec_name`, `default_value`, `should_minimize`, `aliases`).

    The function will:
      - read from the unified schema dictionary format,
      - perform reverse lookup deduplication via target names, human names, and aliases,
      - update an existing specification or allocate a new numeric string ID,
      - save the updated master dictionary cleanly back to disk.

    Returns the updated master dict wrapper.
    """
    # 1. Normalize input to an iterable list of items from the Pydantic schema
    if hasattr(struc, "new_specifications"):
        items = struc.new_specifications
    else:
        items = list(struc or [])

    if not specifications_table:
        raise ValueError("No unified master specification JSON dictionary provided.")


    # 3. Build fast reverse lookup maps for deduplication scanning
    targetname_to_id = {}
    humanname_to_id = {}
    alias_to_id = {}

    for str_id, details in specifications_table.items():
        # Map target_id (e.g., 'dc_gain' -> "0")
        if "target_id" in details:
            targetname_to_id[details["target_id"]] = str_id
            
        # Map spec_name (e.g., 'dc gain' -> "0")
        if "spec_name" in details:
            humanname_to_id[details["spec_name"].lower()] = str_id
            
        # Map every unique registered alias (e.g., 'voltage gain' -> "0")
        for a in details.get("aliases", []):
            alias_to_id[a.lower()] = str_id
    print("targetname_to_id:", targetname_to_id)
    print("humanname_to_id:", humanname_to_id)
    print("alias_to_id:", alias_to_id)
    old_max_id = float('inf')
    found_id = 0
    affected_ids = []
    # 4. Process each incoming spec item proposed by the LLM Agent
    for it in items:
        try:
            print("it =", it)
            target_name = it.target_id
            spec_name = it.spec_name
            default_value = it.default_value
            should_minimize = bool(getattr(it, "should_minimize", False))
            item_aliases = [a.lower() for a in (it.aliases or [])]
        except Exception:
            print("agent_utils: Error occurred while parsing specification object parameters. Skipping entry.")
            continue

        found_id = None # it is str

        # Rule A: Try to find an match by an alternative lowercased alias
        for a in item_aliases:
            if a in alias_to_id:
                found_id = alias_to_id[a]
                break

        # Rule B: Try to find a match by the standardized target_id name
        if found_id is None and target_name in targetname_to_id:
            found_id = targetname_to_id[target_name]

        # Rule C: Try to find a match by a lowercased human label
        if found_id is None and spec_name.lower() in humanname_to_id:
            found_id = humanname_to_id[spec_name.lower()]

        # Rule D: Genuinely new metric. Calculate max ID and increment
        if found_id is None:
            max_id = max([int(k) for k in specifications_table.keys()] or [-1])
            
            found_id = str(max_id + 1)
            if old_max_id > max_id + 1:
                old_max_id = max_id + 1
            # Initialize empty schema blueprint row for the brand-new index
            specifications_table[found_id] = {
                "target_id": target_name,
                "spec_name": spec_name,
                "default_value": default_value,
                "should_minimize": should_minimize,
                "aliases": [],
                "contract": {}  # Placeholder for the data contract block
            }

        # 5. Perform clean object updates/merges on the matched/created ID row
        specifications_table[found_id]["default_value"] = default_value
        specifications_table[found_id]["should_minimize"] = should_minimize
        
        # Merge old and new aliases cleanly without duplicates
        existing_aliases = [a.lower() for a in specifications_table[found_id].get("aliases", [])]
        merged_aliases = list(dict.fromkeys(existing_aliases + item_aliases))
        specifications_table[found_id]["aliases"] = merged_aliases
        # --- THE CONTRACT INJECTION ADDITION ---
        # Find if a simulation contract matches this spec item (checking spec_name or target_id)
        matching_contract = None
        for contract in (valid_contracts or []):
            c_name_lower = contract.spec_name.lower()
            
            # Clean up common noise terms like " (for vcos)" to prevent false mismatches
            c_name_cleaned = c_name_lower.split(" (")[0].replace("and", "&").strip()
            item_name_cleaned = spec_name.lower().replace("and", "&").strip()
            
            # Check if any of our keys match or cross-intersect as substrings
            possible_item_keys = [item_name_cleaned, target_name.lower()] + item_aliases
            
            if any(key in c_name_cleaned or c_name_cleaned in key for key in possible_item_keys if key):
                matching_contract = contract
                break
        
        # If found, serialise the Pydantic structural data into the row entry
        if matching_contract:
            specifications_table[found_id]["contract"] = {
                "sim_type": matching_contract.sim_type,
                "how_to_measure": matching_contract.how_to_measure,
                "csv_filenames": matching_contract.csv_filenames,
                "expected_columns": matching_contract.expected_columns,
                "python_function_name": matching_contract.python_function_name
            }
        elif "contract" not in specifications_table[found_id]:
            # Keep empty if no match and it wasn't pre-existing
            specifications_table[found_id]["contract"] = {}
        if found_id not in affected_ids:
            affected_ids.append(found_id)

    # 6. Repackage into master container envelope structure
    updated_spec_id_unified = {
        "specifications": specifications_table
    }

    # 7. Ensure target folder exists and write safely to disk
    is_test = False
    if spec_tables_path and not is_test:
        out_dir = os.path.dirname(spec_tables_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        
        with open(spec_tables_path, "w", encoding="utf-8") as f:
            json.dump(updated_spec_id_unified, f, ensure_ascii=False, indent=2)

    if old_max_id != float('inf') and found_id is not None:
        for i in range(int(old_max_id), int(found_id) + 1):
            if f'{i}' in specifications_table:
                print(f"Updated/New ID Entry {i}:", specifications_table[f'{i}'])

    return updated_spec_id_unified, affected_ids

def make_dictionary_from_specifications(name, specifications_table):
    return {int(k): v[name] for k, v in specifications_table.items()}

def trim_spec_table(text, num_id_spec_name_dict, aliases):
    trimmed_dict = {}
    text_lower = text.lower()
    
    # Mapping common abbreviations found in text to their full dictionary equivalents
    
    # aliases = local_config.table_specs_aliases
    # target_dict = local_config.table_specs_id

    for num_id, spec_full_name in num_id_spec_name_dict.items():
        spec_lower = spec_full_name.lower()
        
        # 1. Base check: Does the full string name or part of it appear in the markdown text?
        # Clean up parentheses for a softer string search
        clean_name = re.sub(r'\(.*?\)', '', spec_lower).strip()
        exact_match = clean_name in text_lower or spec_lower in text_lower
        
        # 2. Alias check: Does an abbreviation (like PM or PSRR) appear?
        alias_match = False
        if num_id in aliases:
            alias_match = any(alias in text_lower for alias in aliases[num_id])
            
        # 3. Negation Check: Ensure phrases like "CMRR is not applicable" remove it
        # This checks if the spec name or its aliases are followed by negative keywords
        keywords_to_check = [clean_name, spec_lower] + aliases.get(num_id, [])
        is_negated = False
        for kw in keywords_to_check:
            if kw in text_lower:
                # Looks for "keyword is not", "keyword not required", or "not applicable" near it
                if re.search(rf"{re.escape(kw)}[\s\w]*is\s+not", text_lower) or \
                   re.search(rf"{re.escape(kw)}[\s\w]*not\s+applicable", text_lower):
                    is_negated = True
                    break

        # If it matches and isn't explicitly ruled out, add it to our active list
        if (exact_match or alias_match) and not is_negated:
            trimmed_dict[num_id] = spec_full_name
            
    return trimmed_dict

def get_required_spec_contracts(trimmed_spec_table, specifications_table):
    required_num_id_specs_with_contracts = {}
    required_builtin_num_id_specs = {}

    for num_id, spec_name in trimmed_spec_table.items():
        category = specifications_table[str(num_id)]
        contract = category.get("contract", {})

        item = {
            "target_id": category["target_id"],
            "spec_name": category["spec_name"],
        }

        if contract:
            item["contract"] = contract
            required_num_id_specs_with_contracts[int(num_id)] = item
        else:
            required_builtin_num_id_specs[int(num_id)] = item

    return required_builtin_num_id_specs, required_num_id_specs_with_contracts

def get_list_min_targets(specifications_table):  
    list_min_targets = []
    for num_id, spec in specifications_table.items():
        # print(f"Checking spec {num_id}: {spec.get('should_minimize')} for minimization requirement.")
        if spec.get("should_minimize"):
            list_min_targets.append(spec["target_id"])
    return list_min_targets