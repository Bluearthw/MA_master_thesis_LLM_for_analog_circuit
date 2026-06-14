from genai_agent.data import local_config
from genai_agent.data import response_schema
from utils import agent_utils
import os
import shutil
import datetime
from utils import gen_utils
import tempfile
from typing import Optional, Dict, Any
from pydantic import BaseModel

def compress_agent_flow(debug_history, general_rules, category_num):
    contents = f"""## INPUT DATA
### 1. Current Category State:{general_rules}

### 2. Structured Debug History:{debug_history}
# System Prompt: Knowledge Curator & Rule Compression Agent
## Purpose
You are an advanced Knowledge Curator for an automated SPICE circuit design and simulation pipeline. Your job is to analyze structured debugging histories (errors encountered, LLM reasoning, and the successful fixes applied) and distill them into compact, reusable, and non-redundant architectural rules. These rules will be fed back into the Netlist Builder (to prevent errors) and the Debug Agent (to fix errors faster).
## Instructions & Core Logic
1. **Analyze**: Review the **Structured Debug History** (specifically looking at the final iterations where the fix succeeded). Cross-reference the raw `error` with the `analysis` and the code `diff` to pinpoint the exact root cause and its concrete engineering solution.
2. **De-duplicate**: Review the existing rules in the "Current Category State". 
   - If a rule covering this error *already exists*, do not create a new one. Instead, optimize or broaden the existing rule's phrasing or keywords to include this new case.
   - If the error is *entirely new*, draft a fresh rule.
3. **Distill**: Keep rules highly engineering-focused, concise, and actionable. Avoid conversational language. Reference specific SPICE components or netlist syntax constraints revealed in the `diff` if applicable.
4. **Action Assignment**: 
   - Create a proactive instruction for `generation_guidelines` to ensure the generator avoids this mistake next time.
   - Create an error-keyword-mapped item for the `debug_knowledge_base` so the debugger knows what to do if it slips through."""
    # Delegate retry/backoff and error handling to a central helper.
    try:
        struc = agent_utils.call_agent(contents=contents, response_schema=response_schema.Struct_compress)

        # Validate structure
        normalized = validate_struct_compress(struc)
        gen_updates = normalized.get('generation_guidelines_updates')
        kb_updates = normalized.get('debug_kb_updates')

        prompts_path = os.path.join(local_config.path_prompts, 'workflow_prompts.json')
        # Backup existing prompts json
        backup_path = _backup_prompts(prompts_path)

        # Load current prompts structure or create base
        prompts = gen_utils.get_dict_from_json(prompts_path)

        # Ensure top-level structure
        # if category_num == 40 or category_num == 7:# no need to combine
        #     category_num = 1
        cat_key = f'category_{category_num}'
        _ensure_prompt_structure(prompts, cat_key)


        applied = {'generation': None, 'debug_kb': None}
        applied['generation'] = _apply_generation_updates(prompts, gen_updates, cat_key)
        applied['debug_kb'] = _apply_debug_kb_updates(prompts, kb_updates, cat_key)
       
        # Save updated prompts JSON
        _save_prompts(prompts, prompts_path)
        # Write a small log for audit
        _write_audit_log(local_config.path_prompts, category_num, normalized.get('analysis', ''), applied)

        return applied
    except Exception as e:
        # Re-raise so upstream code can decide how to handle persistent failures.
        print(f"compress_agent_flow: call_agent failed: {e}")
        raise


def _build_system_prompt(debug_history, general_rules) -> str:
    return f"""## INPUT DATA
### 1. Current Category State:{general_rules}

### 2. Structured Debug History:{debug_history}
# System Prompt: Knowledge Curator & Rule Compression Agent
## Purpose
You are an advanced Knowledge Curator for an automated SPICE circuit design and simulation pipeline. Your job is to analyze structured debugging histories (errors encountered, LLM reasoning, and the successful fixes applied) and distill them into compact, reusable, and non-redundant architectural rules. These rules will be fed back into the Netlist Builder (to prevent errors) and the Debug Agent (to fix errors faster).
## Instructions & Core Logic
1. **Analyze**: Review the **Structured Debug History** (specifically looking at the final iterations where the fix succeeded). Cross-reference the raw `error` with the `analysis` and the code `diff` to pinpoint the exact root cause and its concrete engineering solution.
2. **De-duplicate**: Review the existing rules in the "Current Category State". 
   - If a rule covering this error *already exists*, do not create a new one. Instead, optimize or broaden the existing rule's phrasing or keywords to include this new case.
   - If the error is *entirely new*, draft a fresh rule.
3. **Distill**: Keep rules highly engineering-focused, concise, and actionable. Avoid conversational language. Reference specific SPICE components or netlist syntax constraints revealed in the `diff` if applicable.
4. **Action Assignment**: 
   - Create a proactive instruction for `generation_guidelines` to ensure the generator avoids this mistake next time.
   - Create an error-keyword-mapped item for the `debug_knowledge_base` so the debugger knows what to do if it slips through."""


def validate_struct_compress(struc: Any) -> Dict[str, Any]:
    """Normalize Struct_compress safely into a predictable dict."""
    # If it's a Pydantic object, dump it to a dict
    if isinstance(struc, BaseModel):
        return struc.model_dump()
    
    # If it's already a dict, return it, fallback to default schema if missing keys
    if isinstance(struc, dict):
        return {
            "analysis": struc.get("analysis", ""),
            "generation_guidelines_updates": struc.get("generation_guidelines_updates"),
            "debug_kb_updates": struc.get("debug_kb_updates")
        }
    
    # Ultimate safe fallback
    return {"analysis": "", "generation_guidelines_updates": None, "debug_kb_updates": None}


def _backup_prompts(prompts_path: str) -> Optional[str]:
    try:
        os.makedirs(os.path.dirname(prompts_path), exist_ok=True)
        if os.path.exists(prompts_path):
            backup_path = prompts_path + '.bak'
            shutil.copyfile(prompts_path, backup_path)
            return backup_path
    except Exception as e:
        print(f"Warning: could not backup prompts file: {e}")
    return None


def _ensure_prompt_structure(prompts: Dict[str, Any], cat_key: str):
    if 'general_rules' not in prompts:
        prompts['general_rules'] = []
    if cat_key not in prompts:
        prompts[cat_key] = {'generation_guidelines': [], 'debug_knowledge_base': {}}


def _apply_generation_updates(prompts: Dict[str, Any], gen_updates: Any, cat_key: str) -> Dict[str, Any]:
    applied = {'action': 'NONE'}
    if gen_updates is None:
        return applied

    action = getattr(gen_updates, 'action', None) if not isinstance(gen_updates, dict) else gen_updates.get('action')
    rule_text = getattr(gen_updates, 'rule_text', None) if not isinstance(gen_updates, dict) else gen_updates.get('rule_text')

    if action == 'APPEND' and rule_text:
        text = rule_text.strip()
        if text not in prompts['general_rules']:
            prompts['general_rules'].append(text)
        if text not in prompts[cat_key].get('generation_guidelines', []):
            prompts[cat_key].setdefault('generation_guidelines', []).append(text)
        applied = {'action': 'APPEND', 'rule': text}

    elif action == 'MODIFY' and rule_text:
        text = rule_text.strip()
        replaced = False
        for idx, existing in enumerate(prompts[cat_key].get('generation_guidelines', [])):
            if text.split('\n')[0].strip() in existing:
                prompts[cat_key]['generation_guidelines'][idx] = text
                replaced = True
                break
        if not replaced:
            for idx, existing in enumerate(prompts.get('general_rules', [])):
                if text.split('\n')[0].strip() in existing:
                    prompts['general_rules'][idx] = text
                    replaced = True
                    break
        applied = {'action': 'MODIFY', 'rule': text, 'replaced': replaced}

    return applied


def _apply_debug_kb_updates(prompts: Dict[str, Any], kb_updates: Any, cat_key: str) -> Dict[str, Any]:
    applied = {'action': 'NONE'}
    if kb_updates is None:
        return applied

    action = getattr(kb_updates, 'action', None) if not isinstance(kb_updates, dict) else kb_updates.get('action')
    keywords = getattr(kb_updates, 'target_keywords', None) if not isinstance(kb_updates, dict) else kb_updates.get('target_keywords')
    action_rule = getattr(kb_updates, 'action_rule', None) if not isinstance(kb_updates, dict) else kb_updates.get('action_rule')

    if action in ('APPEND', 'MODIFY') and keywords and action_rule:
        key = '|'.join(keywords)
        dkb = prompts[cat_key].setdefault('debug_knowledge_base', {})
        if action == 'APPEND':
            if key not in dkb:
                dkb[key] = action_rule.strip()
                applied = {'action': 'APPEND', 'keywords': keywords, 'rule': action_rule}
            else:
                applied = {'action': 'APPEND', 'keywords': keywords, 'skipped': True}
        else:  # MODIFY
            if key in dkb:
                dkb[key] = action_rule.strip()
                applied = {'action': 'MODIFY', 'keywords': keywords, 'rule': action_rule}
            else:
                dkb[key] = action_rule.strip()
                applied = {'action': 'MODIFY', 'keywords': keywords, 'rule': action_rule, 'added': True}

    return applied


def _save_prompts(prompts: Dict[str, Any], prompts_path: str):
    try:
        gen_utils.save_dict_to_json(prompts, prompts_path)
    except Exception as e:
        print(f"Failed to write updated prompts JSON: {e}")


def _write_audit_log(prompts_dir: str, category_num: int, analysis: str, applied: Dict[str, Any]):
    try:
        log_path = os.path.join(prompts_dir, 'compress_update_log.txt')
        with open(log_path, 'a', encoding='utf-8') as lf:
            ts = datetime.datetime.utcnow().isoformat() + 'Z'
            lf.write(f"[{ts}] category={category_num} analysis={analysis}\n")
            lf.write(f"Applied: {applied}\n\n")
    except Exception as e:
        print(f"Warning: could not write log: {e}")


def compress_agent_flow(debug_history, general_rules, category_num):
    """Main entry used in production: calls the agent and persists recommended updates."""
    contents = _build_system_prompt(debug_history, general_rules)
    # Delegate retry/backoff and error handling to central helper.
    try:
        struc = agent_utils.call_agent(contents=contents, response_schema=response_schema.Struct_compress)
    except Exception as e:
        print(f"compress_agent_flow: call_agent failed: {e}")
        raise

    # Then apply updates using the helper functions
    prompts_path = os.path.join(local_config.path_prompts, 'workflow_prompts.json')
    _backup_prompts(prompts_path)
    prompts = gen_utils.get_dict_from_json(prompts_path)
    cat_key = f'category_{category_num}'
    _ensure_prompt_structure(prompts, cat_key)

    normalized = validate_struct_compress(struc)
    gen_updates = normalized.get('generation_guidelines_updates')
    kb_updates = normalized.get('debug_kb_updates')

    applied = {'generation': None, 'debug_kb': None}
    applied['generation'] = _apply_generation_updates(prompts, gen_updates, cat_key)
    applied['debug_kb'] = _apply_debug_kb_updates(prompts, kb_updates, cat_key)

    _save_prompts(prompts, prompts_path)
    _write_audit_log(local_config.path_prompts, category_num, normalized.get('analysis', ''), applied)
    return applied


def compress_agent_flow_with_struct(struct_obj: Any, category_num: int, prompts_path: Optional[str] = None) -> Dict[str, Any]:
    """Apply compress updates using a provided struct (dict or pydantic model).

    This is intended for unit tests where you pass a dummy JSON/dict.
    """
    if prompts_path is None:
        prompts_path = os.path.join(local_config.path_prompts, 'workflow_prompts.json')

    _backup_prompts(prompts_path)
    prompts = gen_utils.get_dict_from_json(prompts_path)
    cat_key = f'category_{category_num}'
    _ensure_prompt_structure(prompts, cat_key)

    normalized = validate_struct_compress(struct_obj)
    gen_updates = normalized.get('generation_guidelines_updates')
    kb_updates = normalized.get('debug_kb_updates')

    applied = {'generation': None, 'debug_kb': None}
    applied['generation'] = _apply_generation_updates(prompts, gen_updates, cat_key)
    applied['debug_kb'] = _apply_debug_kb_updates(prompts, kb_updates, cat_key)

    _save_prompts(prompts, prompts_path)
    _write_audit_log(os.path.dirname(prompts_path), category_num, normalized.get('analysis', ''), applied)
    return applied


def test_compress_flow_with_dummy_json():
    """Quick local test harness that writes a temporary prompts file and runs a dummy struct."""
    # Create temp prompts file
    tmpdir = tempfile.mkdtemp()
    prompts_path = os.path.join(tmpdir, 'workflow_prompts.json')
    # seed with minimal structure
    seed = {'general_rules': ['existing rule 1'], 'category_1': {'generation_guidelines': [], 'debug_knowledge_base': {}}}
    gen_utils.save_dict_to_json(seed, prompts_path)

    dummy = {
        'analysis': 'Dummy analysis: mismatch in model naming',
        'generation_guidelines_updates': {'action': 'APPEND', 'rule_text': 'Rule: use X device naming'},
        'debug_kb_updates': {'action': 'APPEND', 'target_keywords': ['model', 'nmos'], 'action_rule': 'If model name missing, use .model default'}
    }

    applied = compress_agent_flow_with_struct(dummy, category_num=1, prompts_path=prompts_path)
    print('Dummy applied:', applied)
    print('Resulting prompts file:', gen_utils.get_dict_from_json(prompts_path))
    return applied


