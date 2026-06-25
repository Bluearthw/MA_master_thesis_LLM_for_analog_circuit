import os
import re
import sys
import csv
import json
from pathlib import Path
from google.genai import types
sys.path.append(".")
from genai_agent.data import local_config

# region for saving ############################
def save_solutions_csv(run_id, simulation_step, circuit_params, specs, reward):
    # Define the CSV file name based on the run_id to keep it unique
    csv_file_name = f'./solutions/{run_id}/{run_id}.csv'
    # Define the header for the CSV file
    header = ['Simulation step', 'Specs', 'Circuit Params', 'Reward']
    # Prepare the data to be written
    data = [simulation_step, str(specs), str(circuit_params), reward]
    
    try:
        # Check if the CSV file already exists
        file_exists = os.path.isfile(csv_file_name)
        with open(csv_file_name, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # If the file does not exist, write the header first
            if not file_exists:
                writer.writerow(header)
            # Write the data
            writer.writerow(data)
            # write an empty row after each write operation
            writer.writerow([])
    except Exception as e:
        print(f"Error saving solution to CSV: {e}")
    
    return csv_file_name

def save_error_info(path_output_num, cir_num, retry_count, debug_history, status, isCMFB=False, is_differential_output=False, has_input=True):
    metadata_path = path_output_num + "debug_metadata.json"
    
    metadata = {
        "cir_num": cir_num,
        "retry_count": retry_count,
        "status": status,
        "debug_history": debug_history,
        "is_CMFB": isCMFB,
        "is_differential_output": is_differential_output,
        "has_input": has_input
    }
    
    print("path_retry", metadata_path)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

def save_str_to_file(content, path = local_config.path_output + "final_netlist.cir"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(content))
def save_dict_to_json(dict_to_save, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dict_to_save, f, indent=4)

# endregion for saving ############################


# from Mohsen
def writeMd(response: types.GenerateContentResponse, filename: str = "output.md"):
     
    """
    Writes the given markdown string to 'output.md' in the current directory
    and prints a clickable file URI link to open it in VS Code.

    Args:
        my_markdown (str): The markdown content to write to the file.
    """

    # default path
    project_dir = Path(__file__).parent.parent
    path = os.path.join(project_dir, "no_backup", "markdown_files")

    md_string = ""
    # monitoring the thinking summary and the final answer
    for part in response.candidates[0].content.parts:
        if not part.text:
            continue
        if part.thought:
            md_string += f"# Thought Summary\n{part.text}\n"
        else:
            md_string += f"# Answer Text\n{part.text}\n"

    # 2. Get the full, absolute path
    #    Path.resolve() makes it a full path like /home/user/project/output.md
    filepath = Path(path, filename).resolve()

    # 3. Write the markdown to the file
    filepath.write_text(md_string)

    # 4. Convert the path to a clickable file URI
    #    This turns it into file:///home/user/project/output.md
    file_uri = filepath.as_uri()

    # 5. Print the link for the user
    print("\n" + "="*30)
    print(f"\n{file_uri}\n")
    print("="*30 + "\n")

# region for get ############################
def get_file_to_str(path, str=""):
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as file: # https://www.geeksforgeeks.org/python/read-file-as-string-in-python/
                
                circuit_string = file.read() 
                    
                if len(str) > 0:
                    circuit_string = str + circuit_string
                # print(f"Circuit loaded successfully from: {cir_path}")
                return circuit_string
                
        except FileNotFoundError:
            print(f"Error: no files at: {path}")
            raise FileNotFoundError(" No File")
    else:
        return False

        
def get_file_to_lines(path, n_line, start_from_end = False):
    if os.path.isfile(path):
        lines = []
        try:
            with open(path, "r", encoding="utf-8") as file: 
                if start_from_end: # .remove("\n")
                    lines = file.readlines()[-n_line:]
                    # lines.remove('\n') # it removes only 1

                else:
                    lines = file.readlines()[:n_line]
                return lines
                ##################
                # don't use your own function, very slow #
                ###########################
                # line = file.readline()
                # counter = 0
                # while line:
                #     lines.append(line)
                #     line = file.readline()
                #     counter += 1
                #     if counter > n_line:
                #         return lines
                
        except FileNotFoundError:
            print(f"Error: no files at: {path}")
            raise FileNotFoundError(" No File")            
    return []       




def get_dict_from_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to read existing prompts JSON: {e}")
            dict = {}
    return dict

def get_dict_from_json_with_int_keys(path):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return {int(k): v for k, v in json.load(f).items()}
        except Exception as e:
            print(f"Failed to read existing prompts JSON: {e}")
            dict = {}
    else:
        raise ValueError("File not found")
    return dict
# endregion for get ############################

def delete_all_files_except_dir(folder_path):
    """
    Deletes all files in the specified folder.
    Does not remove subdirectories or the folder itself.
    """
    # Validate folder path
    if not os.path.exists(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        return
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a directory.")
        return

    deleted_count = 0
    failed_count = 0

    # Iterate over all items in the folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Only delete files, skip directories!!!!!
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                print(f"Failed to delete '{file_path}': {e}")
                failed_count += 1

    print(f"Deleted {deleted_count} file(s).")
    if failed_count > 0:
        print(f"Failed to delete {failed_count} file(s).")        

