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

missing_specs =  ['Oscillation Frequency', 'Tuning Range & Gain (for VCOs)', 'Phase Noise', 'Output Swing / Amplitude', 'Power Consumption']
impossible_specs =  ['Phase Noise']

is_create = False

if is_create:
    struc_update_table = update_spec_table_agent.update_table_agent_flow(missing_specs)

    print("###struc_update_table = ",struc_update_table)

struc_update_table =  new_specifications=[NewSpecificationItem(target_id='oscillation_frequency',human_name='Oscillation Frequency', aliases=['oscillation frequency', 'f_osc', 'center frequency', 'frequency'], default_value=1000000000.0, should_minimize=False), 
                                          NewSpecificationItem(target_id='vco_tuning_range', human_name='Tuning Range & Gain (for VCOs)', aliases=['tuning range', 'tuning range & gain', 'vco gain', 'vco range'], default_value=100000000.0, should_minimize=False), 
                                          NewSpecificationItem(target_id='phase_noise', human_name='Phase Noise', aliases=['phase noise', 'pn', 'spectral purity'], default_value=-100.0, should_minimize=True), 
                                          NewSpecificationItem(target_id='output_swing', human_name='Output Swing / Amplitude', aliases=['output swing', 'amplitude', 'v_out_peak', 'output voltage swing'], default_value=1.0, should_minimize=False), 
                                          NewSpecificationItem(target_id='power_consumption', human_name='Power Consumption', aliases=['power consumption', 'power', 'pdiss', 'dissipated power'], default_value=0.001, should_minimize=True)]
# agent_utils.update_rest_table(struc_update_table)
def see_tables():
    print(missing_specs)
    missing_specs_updated = [spec for spec in missing_specs if spec not in impossible_specs]
    print(missing_specs_updated)
    
    spec_id_unified = local_config.spec_id_unified
    specifications_table = spec_id_unified["specifications"]
    spec_id_table = {int(k): v["target_id"] for k, v in specifications_table.items()}
        

    # spec_id_table = spec_id_json["table_specs_id"]
    print("###spec_id_table = ", spec_id_table)
    agent_utils.update_tables(struc_update_table, specifications_table,spec_tables_path = None)

see_tables()
