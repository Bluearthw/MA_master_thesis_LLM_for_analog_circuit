from genai_agent.data import local_config
from genai_agent.data import response_schema
from utils import agent_utils
import os
import shutil
import datetime
from utils import gen_utils
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
        gen_updates = getattr(struc, 'generation_guidelines_updates', None)
        kb_updates = getattr(struc, 'debug_kb_updates', None)

        prompts_path = os.path.join(local_config.path_prompts, 'workflow_prompts.json')
        backup_path = prompts_path + '.bak'
        # Backup existing prompts json
        try:
            os.makedirs(local_config.path_prompts, exist_ok=True)
            if os.path.exists(prompts_path):
                shutil.copyfile(prompts_path, backup_path)
        except Exception as e:
            print(f"Warning: could not backup prompts file: {e}")

        # Load current prompts structure or create base
        prompts = {}
        if os.path.exists(prompts_path):
            try:
                prompts = gen_utils.get_dict_from_json(prompts_path)
            except Exception as e:
                print(f"Failed to read existing prompts JSON: {e}")
                prompts = {}

        # Ensure top-level structure
        if 'general_rules' not in prompts:
            prompts['general_rules'] = []
        cat_key = f'category_{category_num}'
        if cat_key not in prompts:
            prompts[cat_key] = {
                'generation_guidelines': [],
                'debug_knowledge_base': {}
            }

        applied = {'generation': None, 'debug_kb': None}

        # Apply generation_guidelines_updates
        if gen_updates is not None:
            action = getattr(gen_updates, 'action', 'NONE')
            rule_text = getattr(gen_updates, 'rule_text', None)
            if action == 'APPEND' and rule_text:
                text = rule_text.strip()
                # append to both top-level and category-specific lists (avoid exact duplicates)
                if text not in prompts['general_rules']:
                    prompts['general_rules'].append(text)
                if text not in prompts[cat_key].get('generation_guidelines', []):
                    prompts[cat_key].setdefault('generation_guidelines', []).append(text)
                applied['generation'] = {'action': 'APPEND', 'rule': text}
            elif action == 'MODIFY' and rule_text:
                text = rule_text.strip()
                # Try to find an existing rule to replace in category first, then top-level
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
                applied['generation'] = {'action': 'MODIFY', 'rule': text, 'replaced': replaced}
            else:
                applied['generation'] = {'action': 'NONE'}

        # Apply debug_kb_updates into category's debug_knowledge_base
        if kb_updates is not None:
            action = getattr(kb_updates, 'action', 'NONE')
            keywords = getattr(kb_updates, 'target_keywords', None) or []
            action_rule = getattr(kb_updates, 'action_rule', None)
            if action in ('APPEND', 'MODIFY') and keywords and action_rule:
                # key by joined keywords
                key = '|'.join(keywords)
                dkb = prompts[cat_key].setdefault('debug_knowledge_base', {})
                if action == 'APPEND':
                    if key not in dkb:
                        dkb[key] = action_rule.strip()
                        applied['debug_kb'] = {'action': 'APPEND', 'keywords': keywords, 'rule': action_rule}
                    else:
                        applied['debug_kb'] = {'action': 'APPEND', 'keywords': keywords, 'skipped': True}
                else:  # MODIFY
                    if key in dkb:
                        dkb[key] = action_rule.strip()
                        applied['debug_kb'] = {'action': 'MODIFY', 'keywords': keywords, 'rule': action_rule}
                    else:
                        # fallback: add it
                        dkb[key] = action_rule.strip()
                        applied['debug_kb'] = {'action': 'MODIFY', 'keywords': keywords, 'rule': action_rule, 'added': True}
            else:
                applied['debug_kb'] = {'action': 'NONE'}

        # Save updated prompts JSON
        try:
            gen_utils.save_dict_to_json(prompts, prompts_path)
        except Exception as e:
            print(f"Failed to write updated prompts JSON: {e}")

        # Write a small log for audit
        try:
            log_path = os.path.join(local_config.path_prompts, 'compress_update_log.txt')
            with open(log_path, 'a', encoding='utf-8') as lf:
                ts = datetime.datetime.utcnow().isoformat() + 'Z'
                lf.write(f"[{ts}] category={category_num} analysis={getattr(struc, 'analysis', '')}\n")
                lf.write(f"Applied: {applied}\n\n")
        except Exception as e:
            print(f"Warning: could not write log: {e}")

        return applied
    except Exception as e:
        # Re-raise so upstream code can decide how to handle persistent failures.
        print(f"compress_agent_flow: call_agent failed: {e}")
        raise
