import os
import csv
import json
from pathlib import Path
from google.genai import types

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

def save_error_info(path_output_num, cir_num, retry_count, debug_history, status, is_CMFB=False):
    metadata_path = path_output_num + "debug_metadata.json"
    
    metadata = {
        "cir_num": cir_num,
        "retry_count": retry_count,
        "status": status,
        "debug_history": debug_history,
        "is_CMFB": is_CMFB
    }
    
    print("path_retry", metadata_path)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)



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