import sys
import importlib

sys.path.append('.')

from testbench.tb_self_healing import functions
from ngspice_interface import dut_testbench
from utils import file_utils
from utils import agent_utils
from genai_agent.workflows import update_spec_table_agent 
from genai_agent.data import local_config
from genai_agent.data.response_schema import NewSpecificationItem
Missing_specifications =  ['Oscillation Frequency', 'Tuning Range & Gain (for VCOs)', 'Phase Noise', 'Output Swing / Amplitude', 'Power Consumption']
Impossible_specifications =  ['Phase Noise']

is_create = False

if is_create:
    struc_update_table = update_spec_table_agent.update_table_agent_flow(Missing_specifications)

    print("###struc_update_table = ",struc_update_table)

struc_update_table =  new_specifications=[NewSpecificationItem(target_id_name='oscillation_frequency', aliases=['oscillation frequency', 'f_osc', 'center frequency', 'frequency'], default_value=1000000000.0, should_minimize=False), 
                                          NewSpecificationItem(target_id_name='vco_tuning_range', aliases=['tuning range', 'tuning range & gain', 'vco gain', 'vco range'], default_value=100000000.0, should_minimize=False), 
                                          NewSpecificationItem(target_id_name='phase_noise', aliases=['phase noise', 'pn', 'spectral purity'], default_value=-100.0, should_minimize=True), 
                                          NewSpecificationItem(target_id_name='output_swing', aliases=['output swing', 'amplitude', 'v_out_peak', 'output voltage swing'], default_value=1.0, should_minimize=False), 
                                          NewSpecificationItem(target_id_name='power_consumption', aliases=['power consumption', 'power', 'pdiss', 'dissipated power'], default_value=0.001, should_minimize=True)]

# agent_utils.update_rest_table(struc_update_table)
def see_tables():
    
    spec_table_path = ".\genai_agent\data\spec_tables\spec_tables_combined.json"
    spec_id_json = file_utils.get_dict_from_json(spec_table_path)
    print("###spec_id_json = ", spec_id_json)
    spec_id_table = spec_id_json["table_specs_id"]
    print("###spec_id_table = ", spec_id_table)

see_tables()
