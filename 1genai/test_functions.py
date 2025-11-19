from google import genai
from google.genai import types
import os
import utils
from pydantic import BaseModel, Field


def test_clean():
    for i in range(5,80):
        cir_path = f"../material/dataset/tb_dataset/{i}/{i}.cir"
        # print(i)
        # print("cir_path",cir_path)
        if not os.path.isfile(cir_path):
            continue
        circuit_string = utils.get_file_to_str(
            cir_path, "" 
        )
        circuit_string = utils.clean_netlist(circuit_string)
        print(circuit_string)
