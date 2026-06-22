import json
import os
import sys
sys.path.append('.')
# Import the tables from local_config
from genai_agent.data import local_config

out_dir = os.path.dirname(__file__)
os.makedirs(out_dir, exist_ok=True)

# 1. Initialize the new single-dictionary structure
unified_specifications = {}

# 2. Iterate through your primary keys (using table_target_id as the baseline)
for k, target_id in local_config.table_target_id.items():
    # Safely extract matching values from the other parallel tables
    spec_name = local_config.table_specs_id.get(k, target_id.replace("_", " ").title())
    default_val = local_config.table_targets_default_values.get(k, 0.0)
    aliases_list = local_config.table_specs_aliases.get(k, [])
    
    # Check if this target string is present in the minimization list
    should_minimize = target_id in local_config.list_targets_to_min

    # 3. Package it into a single clean object under a stringified ID key
    unified_specifications[str(k)] = {
        "target_id": target_id,
        "spec_name": spec_name,
        "default_value": default_val,
        "should_minimize": should_minimize,
        "aliases": aliases_list
    }

# Wrap it in a master dictionary
combined_master = {
    "specifications": unified_specifications
}

# 4. Save to disk
out_path = os.path.join(out_dir, "spec_tables_unified.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(combined_master, f, ensure_ascii=False, indent=2)

print("Wrote unified database to:", out_path)
print(f"Migrated {len(unified_specifications)} specifications successfully into a single table!")