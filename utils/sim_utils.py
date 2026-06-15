import subprocess
import io
import contextlib
import numpy as np
from PySpice.Spice.NgSpice.Shared import NgSpiceShared
import file_utils
from genai_agent.data import local_config

# region for pyspice
def get_vector_and_make_array(plot, name):

    array = np.array(plot[name]._data)
    # array = np.array(vec.array)
    return array

def pyspice_op_sim_simple(circuit, node="vout1"):
    try:
        ngspice = NgSpiceShared.new_instance()
        ngspice.load_circuit(circuit)
        ngspice.run()
        print("simple :: Simulation completed successfully.")
    except Exception as e:
        print(f'Exception: {e}')


def pyspice_op_sim(circuit, node="vout1"):

    
    # Capture both stdout and stderr to detect ngspice errors
    stdout_capture = io.StringIO()
    try:
        ngspice = NgSpiceShared.new_instance()
        
        # Redirect both stdout and stderr to capture any messages
        with contextlib.redirect_stdout(stdout_capture):
            ngspice.load_circuit(circuit)
            ngspice.run()
        
        # Check for errors in captured output
        stdout_output = stdout_capture.getvalue()
        combined_output = stdout_output 
        
        # Check for various error indicators (case-insensitive)
        error_keywords = ["error", "no such", "command available", "illegal", "bad", "unable", "failed"]
        for keyword in error_keywords:
            if keyword.lower() in combined_output.lower():
                return {"success": False, "message": combined_output.strip()}
        
        # Also check stdout from ngspice object
        ngspice_stdout = ngspice.stdout if hasattr(ngspice, 'stdout') else ""
        for keyword in error_keywords:
            if keyword.lower() in ngspice_stdout.lower():
                return {"success": False, "message": ngspice_stdout.strip()}
        
        return {"success": True, "message": "Simulation OK"}
    except Exception as e:
        stdout_output = stdout_capture.getvalue()
        error_msg = (stdout_output).strip() if stdout_output else str(e)
        return {"success": False, "message": error_msg}
    finally:
        stdout_capture.close()

def pyspice_op_sim_final(circuit):
    pyspice_op_sim_simple(circuit)
    file_utils.delete_all_files_except_dir(local_config.path_output)
    # Use a single string buffer for all stdout/stderr
    log_capture = io.StringIO()
    
    try:
        ngspice = NgSpiceShared.new_instance()
        
        with contextlib.redirect_stdout(log_capture), contextlib.redirect_stderr(log_capture):
            ngspice.load_circuit(circuit)
            ngspice.run()
        
        # NgSpice often stores the last output in its own internal stdout
        output_log = log_capture.getvalue().strip()
        # Filter out known benign gmin-stepping chatter (reduces spam in output)
        filtered_lines = []
        for line in output_log.splitlines():
            low = line.lower()
            if "trying" in low:
                continue

            # Keep other notes; only remove gmin-stepping noise
            filtered_lines.append(line)
        output_log = "\n".join(filtered_lines).strip()

        print("====NgSpice Output Log:\n", output_log)
        # Logic: If the log contains common failure signatures 
        # OR if the simulation didn't produce expected results
        if any(err in output_log.lower() for err in ["error", "failed", "no such command", "warning"]):
            return {"success": False, "message": output_log}

        return {"success": True, "message": "Simulation OK\n" + output_log}

    except Exception as e:
        return {"success": False, "message": f"Python Exception: {str(e)}"}
    finally:
        log_capture.close()
# endregion pyspice

# region ngspice

def run_ngspice_direct(netlist_content, is_save = True, path_nl = local_config.path_output +  "test_netlist.cir"):
    # 1. Save netlist to a temporary file
    if is_save:
        path_nl = f"{local_config.path_output}/temp_circuit.cir"
        with open(path_nl, "w") as f:
            f.write(netlist_content)
        
    path_ngspice = r'D:/1kulStudy/8MA_Thesis/tool/Spice64/bin/ngspice_con.exe'  # Update this path to your ngspice executable

    #output log stdout is not useful
    try:
        max_attempts = 2
        for attempt in range(1, max_attempts + 1):
            try:
                process = subprocess.run(
                    [path_ngspice, "-b", "-n", path_nl],
                    capture_output=True,
                    text=True,
                    shell=False,
                    timeout=15
                )
                break
            except subprocess.TimeoutExpired:
                if attempt < max_attempts:
                    print(f"[run_ngspice_direct] Timeout on attempt {attempt}. Retrying...")
                    continue
                print(f"[run_ngspice_direct] Timeout on attempt {attempt}. Giving up.")
                return {"success": False, "message": "Simulation timed out"}

        if 'process' not in locals():
            return {"success": False, "message": "Simulation did not run"}

        # Combine stdout and stderr for analysis
        logs = process.stderr if process.stderr and process.stderr.strip() else ""

        # if logs:
        #     print("--- Simulation Log (stderr) ---")
        #     print(logs)
        error_log_lower = logs.lower()

        # Determine if this is a real error or just a warning
        # Check for fatal errors
        has_fatal_error = "fatal error" in   error_log_lower
        has_error = "no such" in error_log_lower or "error" in error_log_lower or "warning" in error_log_lower 
        # Exclude the "dc value used for op" warning - it's not a real error
        is_dc_value_warning = "note" in error_log_lower

        filtered_lines = [
            line for line in error_log_lower.splitlines() 
            if not line.strip().lower().startswith("note:")
        ]
        clean_log = "\n".join(filtered_lines)

        # If there's a fatal error, check error details even if exit code is 0
        if has_fatal_error:
            # print(f"--- FATAL ERROR DETECTED ---")
            print(f"Error Details: {logs}")
            return {"success": False, "message": f"Simulation failed\n{logs}"}

        # print(f"=== Simulation Analysis ---{is_dc_value_warning}, fatal {has_fatal_error}")
        # If only a dc value warning (no fatal error), treat as success
        if has_error:
            # print("--- Simulation completed with warnings (non-fatal) ---")
            return {"success": False, "message": clean_log}
        if is_dc_value_warning:
            # print("--- Simulation completed with warnings (non-fatal) ---")
            return {"success": True, "message": f"Simulation OK\n{logs}"}

        # Check exit code for crash #????? never see 0
        if process.returncode != 0:
            print(f"--- CRASH DETECTED (Exit Code: {process.returncode}) ---")
            error_msg = logs if logs else "Segmentation Violation (Hard Crash)"
            print(f"Error Details: {error_msg}")
            return {"success": False, "message": f"Simulation failed (Exit Code: {process.returncode})\n{error_msg}"}

        # Normal success case
        return {"success": True, "message": f"Simulation OK\n{logs}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def run_ngspice_direct_from_final_netlist(num = 4):
    path_nl = local_config.path_output +  f"{num}/final_netlist.cir"
    netlist = file_utils.get_file_to_str(path_nl)
    # utils.delete_all_files_skip_dir(local_config.path_output) # delete all previous output to avoid confusion
    
    success = run_ngspice_direct(netlist, False, path_nl) # will not overwrite temp_netlist
    print("==netlist",netlist)
    if success["success"]:
        print("Simulation successful!")
    else:
        print("Simulation failed with message:", success["message"])
# endregion ngspice

