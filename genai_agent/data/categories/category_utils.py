import re
import os
import sys
sys.path.append(".")
from utils import gen_utils
from genai_agent.data.local_config import path_category_md
from genai_agent.data.local_config import path_categories
from utils import file_utils
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
    print("lines:", lines)
    print("category:", category)
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
        if 'rule' in line.lower():
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

def category_str_extract_line(category_str):
    if not category_str:
        return {"category": "", "required_specs": []}

    lines = category_str.splitlines()
    category = ""
    required_specs = []

    # 1) Find first markdown heading and use it as category title
    for line in lines:
        m = re.match(r"^\s*#{1,6}\s*(?:\d+\.?\s*)?(.*\S.*)$", line)
        if m:
            # keep the whole heading line (including leading #'s and numbering)
            category = line.strip()
            break
    # print("lines:", lines)
    print("category:", category)
    # 2) Find a Measurements (or Stimuli/Measurements) section and collect bullets
    start_idx = None
    end_idx = None
    meas_count = 0
    for i, line in enumerate(lines):
        low = line.lower()
        print("low:", low)
        if 'measurement' in low and meas_count < 2:
            # start from the line after the heading that mentions measurements
            start_idx = i + 1
            meas_count += 1

        if 'topologies' in low or 'rule' in low:
            end_idx = i
            if not start_idx is None:
                break
    print(start_idx)
    print(end_idx)
    sys.exit(0)
    # Collect raw bullet lines (keep the whole line, trimmed of trailing newline)
    if start_idx is not None:
        i = start_idx
        if end_idx is None:
            end_idx = len(lines)
        while i < end_idx:
            l = lines[i]
            # Accept bullets that start with '*', '-', '+' (possibly indented)
            if re.match(r"^\s*[\*\-\+]\s+", l):
                # l is the raw line from file
                # normalize NBSP -> space
                l_clean = l.replace('\u00A0', ' ')
                # remove leading bullet marker and surrounding whitespace
                l_clean = re.sub(r'^\s*[\*\-\+]\s*', '', l_clean)
                # remove bold/italic markdown markers but keep text inside
                l_clean = re.sub(r'\*{1,2}(.+?)\*{1,2}', r'\1', l_clean)
                # collapse multiple whitespace to single space and trim
                l_clean = re.sub(r'\s+', ' ', l_clean).strip()
                required_specs.append(l_clean)
                i += 1
                continue

            # Skip blank lines
            if l.strip() == "":
                i += 1
                continue

            # Stop if we hit another heading or top-level non-list content
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
    return {"category": category, "required_specs": deduped}
def make_category_json():
    json_path = path_categories + "line_jsons/"
    print("dir exists:", os.path.isdir(json_path))
    for i in range(36,37):
        print(i)
        cat_str = file_utils.get_file_to_str(path_category_md + f'{i}.md')
        # print(cat_str)
        cat_dict = category_str_extract_line(cat_str)
        print(cat_dict)
        file_utils.save_dict_to_json(cat_dict, json_path + f'category{i}.json')

make_category_json()