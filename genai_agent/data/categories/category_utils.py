import re
import os
import sys
sys.path.append(".")
from utils import gen_utils
from genai_agent.data.local_config import path_category
from genai_agent.data.local_config import path_categories
def split_category():
    # Read the source file
    with open('classes_final_revised.md', 'r') as f:
        content = f.read()

    # Split by ### followed by number.
    sections = re.split(r'(?=### \d+\.)', content)

    # Create each category file
    for section in sections[1:]:  # skip the first if empty
        match = re.match(r'### (\d+)\.', section)
        if match:
            num = match.group(1)
            filename = f'category{num}.md'
            with open(filename, 'w') as f:
                f.write(section.strip())
            print(f'Created {filename}')


def category_str_extract(category_str):
    """Extract a category title and required specs from a category markdown string.

    Returns a dict: {"category": <title str>, "required_specs": [spec1, spec2, ...]}

    The function tries to find the first Markdown heading and uses that as the
    category title. It then looks for a "Measurements" (or similar) section and
    extracts the subsequent bullet items as required specs. If nothing is
    found, returns empty strings/lists.
    """
    if not category_str:
        return {"category": "", "required_specs": []}

    lines = category_str.splitlines()
    category = ""
    required_specs = []

    # 1) Find first markdown heading and use it as category title
    for line in lines:
        m = re.match(r"^\s*#{1,6}\s*(?:\d+\.?\s*)?(.*\S.*)$", line)
        if m:
            category = m.group(1).strip()
            break

    # 2) Find a Measurements (or Stimuli/Measurements) section and collect bullets
    start_idx = None
    end_idx = None
    meas_count = 0
    for i, line in enumerate(lines):
        if 'measurement' in line.lower() and meas_count < 2:
            start_idx = i + 1
            meas_count += 1 

        if 'topologies' in line.lower():
            end_idx = i
            
            break

    
    if start_idx is not None:
        i = start_idx
        if end_idx is not None:
            end_idx = min(end_idx, len(lines))
        while i < end_idx:
            l = lines[i]
            # Accept list bullets ("*", "-", "+") possibly indented
            if re.match(r"^\s*[\*\-\+]\s+", l):
                # Remove bullet marker
                s = re.sub(r"^\s*[\*\-\+]\s+", "", l).strip()
                # Try to capture the spec name before a trailing colon
                m = re.match(r"\*{0,2}\s*(?P<name>[^:\*]+?)\s*\*{0,2}\s*:\s*(.*)$", s)
                if m:
                    name = m.group('name')
                else:
                    # Fallback: take up to first ':' or the whole line
                    m2 = re.match(r"(?P<name>[^:]+):", s)
                    if m2:
                        name = m2.group('name')
                    else:
                        name = s

                # Clean markdown emphasis and math markers
                name = re.sub(r"[\*_\$]", "", name).strip()
                if name:
                    required_specs.append(name)
                i += 1
                continue

            # skip blank or comment lines
            if l.strip() == "":
                i += 1
                continue

            # stop if we hit another top-level section (heading) or non-list content
            if re.match(r"^\s*#{1,6}\s+", l) or re.match(r"^\S", l):
                break
            i += 1

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for s in required_specs:
        if s not in seen:
            seen.add(s)
            deduped.append(s)
    # print(f"Category: {category}, Required Specs: {required_specs}")
    return {"category": category, "required_specs": deduped}

def make_category_json():
    json_path = path_categories + "jsons/"
    print("dir exists:", os.path.isdir(json_path))
    for i in range(1,2):
        print(i)
        cat_str = gen_utils.get_file_to_str(path_category + f'{i}.md')
        # print(cat_str)
        cat_dict = category_str_extract(cat_str)
        print(cat_dict)
        gen_utils.save_dict_to_json(cat_dict, json_path + f'category{i}.json')

make_category_json()