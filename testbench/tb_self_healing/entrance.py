import sys
import importlib

sys.path.append('.')

from testbench.tb_self_healing import functions
from utils import file_utils
from utils import gen_utils

def heal_agent(missing_id):
    print(f"[Heal] ID {missing_id} not found. Modifying functions.py...")
    
    # Define our new sub-function name based on a prompt or requirement
    new_sub_func = f"get_requirement_{missing_id}"
    
    # 1. Read the existing functions.py file
    with open("./testbench/tb_self_healing/functions.py", "r") as f:
        content = f.read()
    print(content)
    # 2. Build the new if/elif branch string and the new function definition
    new_branch = f"elif id == {missing_id}:\n        return {new_sub_func}()\n    # [INSERT_NEW_BRANCH_HERE]"
    
    new_function_def = f"\n\ndef {new_sub_func}():\n    return {missing_id} * 10  # Automatically healed\n"
    
    # 3. Inject the code using our marker comment replacement
    updated_content = content.replace("# [INSERT_NEW_BRANCH_HERE]", new_branch)
    updated_content += new_function_def
    print(f"[Heal] Updated content:\n{updated_content}")
    # 4. Write back to functions.py
    with open("./testbench/tb_self_healing/functions.py", "w") as f:
        f.write(updated_content)
        
    # 5. Read, update, and save the json table mapping
    table = file_utils.get_dict_from_json_with_int_keys("./testbench/tb_self_healing/table.json")
    table[missing_id] = new_sub_func
    # Assuming file_utils has a save method:
    file_utils.save_dict_to_json(table, "./testbench/tb_self_healing/table.json")
    
    print("[Heal] Code injected and registry updated successfully.")

def tb_entrance(i):
    # Added module reloading at the start of the check loop
    while True:
        importlib.reload(functions) # Ensure we read freshest hard-drive state
        table = file_utils.get_dict_from_json_with_int_keys("./testbench/tb_self_healing/table.json")
        
        value = None
        # Fixed: table.items must be called with parentheses table.items()
        for k, v in table.items(): 
            if k == i:
                value = v
                break
                
        if value is None:
            heal_agent(i)
            # The loop continues, reloads the new code, and will hit the "else" branch next time!
        else:
            break
            
    # Execute the central routing function
    result = functions.measurement(i)
    print(f"[Entrance] Result for ID {i}: {result}")
    return result
tb_entrance(4)

