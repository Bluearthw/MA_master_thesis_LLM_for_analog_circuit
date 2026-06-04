import os
import csv
import json

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

def save_error_info(path_output_num, cir_num, retry_count, error_history, fix_info, status, is_CMFB=False):
        metadata_path = path_output_num + "debug_metadata.json"
        metadata = {
            "cir_num": cir_num,
            "retry_count": retry_count,
            "status": status,
            "error_history": error_history,
            "fix_info": fix_info,
            "is_CMFB": is_CMFB
        }
        print("path_retry",metadata_path)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)