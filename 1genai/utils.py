from google import genai
from local_config import GOOGLE_API_KEY
def get_client():
    client = genai.Client(api_key = GOOGLE_API_KEY)
    return client

def get_file_to_str(path, str, str2=""):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            circuit_string = str + str2 + f.read() 
        # print(f"Circuit loaded successfully from: {cir_path}")
            return circuit_string
    except FileNotFoundError:    
        print(f"Error: no files at: {path}")

def check_file_and_overwrite(path, msg):
    with open(f"{path}", "w") as f:
        f.write(f"{msg}")