import sys
sys.path.append(".")
from utils import yaml_creation

"""9 target
targets:
  area: !!float 2.0e-03
  bandwidth: !!float 10.00
  current: !!float 2.0e-01
  dc_gain: !!float 1.00
  gain_margin: !!float 4.00
  noise_total: !!float 3.0
  phase_margin: !!float 0.00
  slew_rate: !!float 15.00
  ugbw: !!float 10.00
"""
def test_get_params(path):
    result = yaml_creation.get_params(path)
    print( result)
    print(len( result))

def test_make_param_lines():
    params = ['Cload', 'VB1', 'VDD', 'l0', 'l1', 'm0', 'm1', 'period', 'trf', 'vcm', 'w0', 'w1']
    print(yaml_creation.make_param_lines(params))


def test_get_targets():
    path_id = {0: './genai_agent/output/155/ac_gain.csv', 1: './genai_agent/output/155/ac_gain.csv', 15: './genai_agent/output/155/ac_gain.csv', 16: './genai_agent/output/155/ac_gain.csv', 5: './genai_agent/output/155/ac_gain.csv', 6: './genai_agent/output/155/ac_gain.csv', 3: './genai_agent/output/155/noise.csv', 4: './genai_agent/output/155/tran_SR.csv', 12: './genai_agent/output/155/tran_SR.csv', 10: './genai_agent/output/155/dc_swing.csv', 11: './genai_agent/output/155/dc_swing.csv', 13: './genai_agent/output/155/dc_icmr.csv', 14: './genai_agent/output/155/ac_cmrr.csv', 2: './genai_agent/output/155/ac_psrr.csv'}
    result = yaml_creation.get_targets(path_id)
    print(result)
    return result

def test_make_targets_lines():
    targets = {'gain': 20, 'bandwidth': 1000000.0, 'ac_gain': 200, 'phase_response': 60.0, 'gm': 45.0, 'phm': 60.0, 'noise': 0.03, 'slew_rate': 15.0, 'settle_time': 10.0, 'input_swing': 0.6, 'output_swing': 0.6, 'icmr': 0.5, 'cmrr': 60.0, 'psrr': 60.0, 'area': 2e-09, 'current': 0.0002}
    result = yaml_creation.make_targets_lines(targets)
    print(result)

def test_make_spec_weights_lines():
    sw = {'gain': 20, 'bandwidth': 1000000.0, 'ac_gain': 200, 'phase_response': 60.0, 'gm': 45.0, 'phm': 60.0, 'noise': 0.03, 'slew_rate': 15.0, 'settle_time': 10.0, 'input_swing': 0.6, 'output_swing': 0.6, 'icmr': 0.5, 'cmrr': 60.0, 'psrr': 60.0, 'area': 2e-09, 'current': 0.0002}
    result = yaml_creation.make_spec_weights_lines(sw)
    print(result)

def test_make_circuit_multipliers():
    params = ['Cload', 'VB1', 'VDD', 'l0', 'l1', 'm0', 'm1', 'period', 'trf', 'vcm', 'w0', 'w1']
    result = yaml_creation.make_circuit_multipliers(params)
    print(result)

def test_make_full_yaml(path, cir_name):
    path_id_9 ={0: './genai_agent/output/9/ac_gain.csv', 1: './genai_agent/output/9/ac_gain.csv', 15: './genai_agent/output/9/ac_gain.csv', 16: './genai_agent/output/9/ac_gain.csv', 21: './genai_agent/output/9/ac_gain.csv', 5: './genai_agent/output/9/ac_gain.csv', 6: './genai_agent/output/9/ac_gain.csv', 3: './genai_agent/output/9/noise.csv', 2: './genai_agent/output/9/psrr.csv', 4: './genai_agent/output/9/tran_SR.csv', 12: './genai_agent/output/9/tran_SR.csv', 22: './genai_agent/output/9/current.csv'}
    # path_id = {0: './genai_agent/output/155/ac_gain.csv', 1: './genai_agent/output/155/ac_gain.csv', 15: './genai_agent/output/155/ac_gain.csv', 16: './genai_agent/output/155/ac_gain.csv', 5: './genai_agent/output/155/ac_gain.csv', 6: './genai_agent/output/155/ac_gain.csv', 3: './genai_agent/output/155/noise.csv', 4: './genai_agent/output/155/tran_SR.csv', 12: './genai_agent/output/155/tran_SR.csv', 10: './genai_agent/output/155/dc_swing.csv', 11: './genai_agent/output/155/dc_swing.csv', 13: './genai_agent/output/155/dc_icmr.csv', 14: './genai_agent/output/155/ac_cmrr.csv', 2: './genai_agent/output/155/ac_psrr.csv'}
    path_id = path_id_9
    path_id = {k: v for k, v in path_id.items() if k != 16}
    result = yaml_creation.make_full_yaml(path, path_ids=path_id, cir_name=cir_name)
    print(result)
# it should work for both .params types
# test_get_params("./genai_agent/output/9/final_netlist.cir")
# test_get_params("D:\\1kulStudy\\8MA_Thesis\\workplace\\ngspice_interface\\files\\input_netlists\\TwoStage.cir")
# test_get_params("D:\\1kulStudy\\8MA_Thesis\\workplace\\genai_agent\\output\\9\\final_netlist.cir")
# test_make_param_lines()

# test_get_targets()
# test_make_targets_lines()
# test_make_spec_weights_lines()
# test_make_circuit_multipliers()
cir_name = "test"
test_make_full_yaml(f"./genai_agent/output/{cir_name}/final_netlist.cir", cir_name)