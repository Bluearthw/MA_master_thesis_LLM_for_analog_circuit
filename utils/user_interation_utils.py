import sys
import os
import time
# region print
def print_status(is_with_RL, test):
    print("##test length:",len(test))
    if is_with_RL == 0:
        print("Only netlist generation is enabled.")
    elif is_with_RL == 1:
        print("Whole workflow is enabled.")
    elif is_with_RL == 2:
        print("Only RL sizer is enabled.")
    elif is_with_RL == 3:
        print("Only yaml creation is enabled.")

# endregion print
# region user input

def user_modify_input(v_name, v_old):
    """Prompt the user to accept or modify a given value.

    Args:
        v_name (str): The name of the value being modified.
        v_old: The current value that may be changed.
    Returns:
        The original value if the user does not modify it, otherwise the new value.
    """
    print(f"Current value: {v_old}")
    choice = input_with_timeout(f"Do you want to modify {v_name}? [y/yes, others are not yes]: ", timeout=10, default="n")
    choice = choice.strip().lower()
    if choice not in ("y", "yes"):
        print("Keeping the original value.")
        return v_old

    v_new = input_with_timeout("Enter new value: ", timeout=10, default="").strip()
    if v_new == "":
        print("No new value entered. Keeping the original value.")
        return v_old
    return v_new

def input_with_timeout(prompt, timeout=10, default=""):
    """Read input with a timeout, returning default if no response."""
    sys.stdout.write(prompt)
    sys.stdout.flush()

    # Windows implementation using msvcrt avoids hanging stdin threads.
    if os.name == 'nt':
        try:
            import msvcrt
        except ImportError:
            msvcrt = None
    
        if msvcrt is not None:
            line = ''
            end_time = time.time() + timeout
            while time.time() < end_time:
                if msvcrt.kbhit():
                    ch = msvcrt.getwch()
                    if ch == '\r' or ch == '\n':
                        sys.stdout.write('\n')
                        sys.stdout.flush()
                        return line
                    if ch == '\x08':
                        if line:
                            line = line[:-1]
                            sys.stdout.write('\b \b')
                            sys.stdout.flush()
                        continue
                    line += ch
                    sys.stdout.write(ch)
                    sys.stdout.flush()
                time.sleep(0.01)
            sys.stdout.write('\n')
            return default
    try:
        # Fallback for non-Windows or if msvcrt is unavailable.
        from threading import Event, Thread

        user_input = {'value': default}
        done = Event()

        def read_input():
            try:
                user_input['value'] = sys.stdin.readline().rstrip('\n')
            except Exception:
                user_input['value'] = default
            finally:
                done.set()

        thread = Thread(target=read_input, daemon=True)
        thread.start()

        for remaining in range(timeout, 0, -1):
            if done.wait(1):
                break
            sys.stdout.write(f"\r{prompt}(auto selecting default in {remaining}s) ")
            sys.stdout.flush()

        sys.stdout.write('\n')
        if done.is_set():
            return user_input['value']
        return default
    except Exception:
        # Fall back to a normal prompt if the timeout helper is unavailable.
        sys.stdout.write(prompt)
        sys.stdout.flush()
        return sys.stdin.readline().rstrip('\n')
    
def user_input_targets(targets):
    """
    Interactive interface for user to review and modify target values.
    
    Args:
        targets (dict): Dictionary of target metrics with default values
        
    Returns:
        dict: Updated targets dictionary with user modifications
    """
    print("\n=== Target Values Review ===")
    print("Current target values:")
    sorted_targets = sorted(targets.items())
    for i, (key, value) in enumerate(sorted_targets, 1):
        print(f"  {i}. {key}: {value}")
    
    while True:
        modify = input_with_timeout("\nDo you want to modify any target values? (y/n): ").strip().lower()
        if modify not in ['y', 'yes']:
            break
            
        try:
            target_num = int(input_with_timeout(f"Enter the number of the target to modify (1-{len(sorted_targets)}): ").strip())
            if target_num < 1 or target_num > len(sorted_targets):
                print(f"Error: Please enter a number between 1 and {len(sorted_targets)}.")
                continue
            target_name = sorted_targets[target_num - 1][0]
        except ValueError:
            print("Error: Please enter a valid number.")
            continue
            
        try:
            new_value = float(input_with_timeout(f"Enter new value for '{target_name}' (current: {targets[target_name]}): ").strip())
            targets[target_name] = new_value
            print(f"Updated {target_name} to {new_value}")
        except ValueError:
            print("Error: Please enter a valid number.")
    
    print("\nFinal target values:")
    for i, (key, value) in enumerate(sorted_targets, 1):
        print(f"  {i}. {key}: {value}")
    
    return targets
# endregion user input


