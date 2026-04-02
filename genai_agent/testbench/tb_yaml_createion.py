import sys
sys.path.append("./genai_agent")

from gen_utils import yaml_creation

def tb_get_params(path):
    result = yaml_creation.get_params(path)
    print( result)
    print(len( result))

# it should work for both .params types
tb_get_params("./genai_agent/output/9/final_netlist.cir")
tb_get_params("D:\\1kulStudy\\8MA_Thesis\\workplace\\ngspice_interface\\files\\input_netlists\\TwoStage.cir")