import json
import os
import sys
sys.path.append('.')
# Import the tables from local_config
from genai_agent.data import local_config

out_dir = os.path.dirname(__file__)
os.makedirs(out_dir, exist_ok=True)

# Convert mappings to JSON-friendly forms (string keys)
combined = {
    "table_specs_id": {str(k): v for k, v in local_config.table_specs_id.items()},
    "table_target_id": {str(k): v for k, v in local_config.table_target_id.items()},
    "table_targets_default_values": {str(k): v for k, v in local_config.table_targets_default_values.items()},
    "table_specs_aliases": {str(k): v for k, v in local_config.table_specs_aliases.items()},
    "list_targets_to_min": local_config.list_targets_to_min,
}

out_path = os.path.join(out_dir, "spec_tables_combined.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(combined, f, ensure_ascii=False, indent=2)

print("Wrote:", out_path)
print("Counts:", "specs=", len(combined["table_specs_id"]), "targets=", len(combined["table_target_id"]), "aliases=", len(combined["table_specs_aliases"]))
