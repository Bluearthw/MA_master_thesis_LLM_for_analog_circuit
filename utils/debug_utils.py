import os
import json
import re
import time
import difflib
from genai_agent.data import local_config
from utils import file_utils


def make_path_id(spec_sims, path_output_num):
    struct_path_id = {}
    for spec_sim in spec_sims:
        path_file = path_output_num + spec_sim.sim_file_name
        if os.path.exists(path_file):
            spec_num_id = spec_sim.spec_num_id
            target = struct_path_id.get(spec_num_id)
            if target is None:
                struct_path_id[spec_num_id] = path_file
            else:
                if not isinstance(target, list):
                    struct_path_id[spec_num_id] = [target, path_file]
                else:
                    struct_path_id[spec_num_id].append(path_file)
        else:
            print(f"File {path_file} does not exist.")
            raise RuntimeError(f"Expected output file {path_file} not found.")
    return struct_path_id


def count_retry_info(cir_nums, json_name="debug_metadata.json"):
    total_retries = 0
    zero_retry_count = 0
    len_cir_nums = len(cir_nums)
    for cir_num in cir_nums:
        path = local_config.path_output + f"{cir_num}/" + json_name
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            retry = data.get("retry_count", -1)
            if retry == 0:
                zero_retry_count += 1
            if retry == -1:
                raise ValueError(f"Invalid retry count in {path}")
            total_retries += retry
    avg_retry = total_retries / len_cir_nums if len_cir_nums > 0 else 0
    return total_retries, avg_retry, zero_retry_count


def reduce_duplicate_str(duplicate_str):
    lines = duplicate_str.splitlines()
    if not lines:
        return ""

    out_lines = []
    prev = lines[0]
    count = 1
    max_count = 0
    for line in lines[1:]:
        if line == prev:
            count += 1
        else:
            out_lines.append(f"{prev} (x{count})" if count > 1 else prev)
            prev = line
            max_count = max(max_count, count)
            count = 1

    out_lines.append(f"{prev} (x{count})" if count > 1 else prev)
    max_count = max(max_count, count)
    print(f"Maximum consecutive duplicates: {max_count}")
    return "\n".join(out_lines)


def get_biggest_rule_number(rules_list):
    numbers = []
    for rule in rules_list:
        match = re.match(r"^(\d+)\.", rule.strip())
        if match:
            numbers.append(int(match.group(1)))
    return max(numbers) if numbers else 0


def get_netlist_diff(error_netlist: str, fixed_netlist: str, context_lines: int = 3) -> str:
    error_lines = error_netlist.splitlines()
    fixed_lines = fixed_netlist.splitlines()
    diff = difflib.unified_diff(
        error_lines,
        fixed_lines,
        fromfile='error_netlist',
        tofile='fixed_netlist',
        n=context_lines,
        lineterm=''
    )
    diff_string = "\n".join(diff)
    return diff_string or "No differences found between the netlists."


def test_delay(sec, msg=""):
    print(f"{msg}: Waited for {sec} seconds")
    time.sleep(sec)
