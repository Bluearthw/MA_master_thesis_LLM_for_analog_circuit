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

struc_update_table =  new_specifications=[NewSpecificationItem(target_id='oscillation_frequency',spec_name='Oscillation Frequency', aliases=['oscillation frequency', 'f_osc', 'center frequency', 'frequency'], default_value=1000000000.0, should_minimize=False), 
                                          NewSpecificationItem(target_id='vco_tuning_range', spec_name='Tuning Range & Gain (for VCOs)', aliases=['tuning range', 'tuning range & gain', 'vco gain', 'vco range'], default_value=100000000.0, should_minimize=False), 
                                          NewSpecificationItem(target_id='phase_noise', spec_name='Phase Noise', aliases=['phase noise', 'pn', 'spectral purity'], default_value=-100.0, should_minimize=True), 
                                          NewSpecificationItem(target_id='output_swing', spec_name='Output Swing / Amplitude', aliases=['output swing', 'amplitude', 'v_out_peak', 'output voltage swing'], default_value=1.0, should_minimize=False), 
                                          NewSpecificationItem(target_id='power_consumption', spec_name='Power Consumption', aliases=['power consumption', 'power', 'pdiss', 'dissipated power'], default_value=0.001, should_minimize=True)]
# agent_utils.update_rest_table(struc_update_table)
def see_tables():
    print(missing_specs)
    missing_specs_updated = [spec for spec in missing_specs if spec not in impossible_specs]
    print(missing_specs_updated)
    # spec_table_path = ".\genai_agent\data\spec_tables\spec_tables_combined.json"
    # spec_id_json = file_utils.get_dict_from_json(spec_table_path)
    # spec_id_json_old = {'table_specs_id': {'0': 'DC Gain', '1': 'Bandwidth', '2': 'Power Supply Rejection Ratio (PSRR)', '3': 'Input equivalent integrated total noise', '4': 'Slew rate', '5': 'Gain margin', '6': 'Phase margin', '7': 'Output total noise', '8': 'Input impedance', '9': 'Output impedance', '10': 'Input swing', '11': 'Output swing', '12': 'Settle time', '13': 'Input Common-Mode Range (ICMR)', '14': 'Common-Mode Rejection Ratio (CMRR)', '16': 'Phase response', '17': 'Common-Mode Gain', '18': 'Differential-Mode Gain (differential output)', '19': 'Output Balance', '20': 'CMFB Loop Stability', '21': 'UGBW, unity gain bandwidth', '22': 'Current', '23': 'DC Output Voltage', '24': 'Line Regulation', '25': 'Load Regulation', '26': 'Temperature Coefficient (TC)', '27': 'Startup Behavior', '28': 'Current Matching', '29': 'Output Ripple', '30': 'Voltage Compliance Range'}, 'table_target_id': {'0': 'dc_gain', '1': 'bandwidth', '2': 'psrr', '3': 'input_total_noise', '4': 'slew_rate', '5': 'gain_margin', '6': 'phase_margin', '7': 'output_total_noise', '8': 'input_impedance', '9': 'output_impedance', '10': 'input_swing', '11': 'output_swing', '12': 'settle_time', '13': 'icmr', '14': 'cmrr', '16': 'phase_response', '17': 'cm_gain', '18': 'dm_gain', '19': 'output_balance', '20': 'cmfb_stability', '21': 'ugbw', '22': 'current', '23': 'dc_output_voltage', '24': 'line_regulation', '25': 'load_regulation', '26': 'temperature_coefficient', '27': 'startup_behavior', '28': 'current_matching', '29': 'output_ripple', '30': 'voltage_compliance'}, 'table_targets_default_values': {'0': 10.0, '1': 100.0, '2': 10.0, '3': 1e-06, '4': 15.0, '5': 45.0, '6': 60.0, '7': 3e-06, '8': 1000000000.0, '9': 1000.0, '10': 0.1, '11': 0.1, '12': 10.0, '13': 0.5, '14': 10.0, '15': 10.0, '16': 60.0, '17': -40.0, '18': 10.0, '19': 1.0, '20': 60.0, '21': 1000000.0, '22': 0.2, '23': 0.2, '24': 100, '25': 5, '26': 800.0, '27': 2, '28': 5, '29': 0.01, '30': 0.3}, 'table_specs_aliases': {'0': ['dc gain', 'voltage gain', 'a_v', 'gain'], '1': ['bandwidth', 'corner frequency', '-3db', 'f3db', 'f_3db'], '2': ['psrr', 'power supply rejection ratio', 'power supply rejection', 'rejection ratio'], '3': ['input equivalent integrated total noise', 'input referred noise', 'input-referred noise', 'integrated total noise', 'noise density', 'input noise'], '4': ['slew rate', 'slew-rate', 'slew'], '5': ['gain margin', 'gm', 'gain margin'], '6': ['phase margin', 'pm', 'phase margin'], '7': ['output noise', 'integrated output noise', 'noise at output', 'output_total_noise'], '8': ['input impedance', 'input resistance', 'input rin'], '9': ['output impedance', 'output resistance', 'output rout'], '10': ['input swing', 'input voltage swing', 'input signal swing'], '11': ['output swing', 'output voltage swing', 'output signal swing'], '12': ['settle time', 'settling time', 'settle_time'], '13': ['input common-mode range', 'icmr', 'common mode range'], '14': ['common-mode rejection ratio', 'cmrr', 'common mode rejection'], '15': ['ac gain', 'ac gain single port output', 'ac gain (single port output)', 'gain at ac'], '16': ['phase response', 'phase shift', 'phase response'], '17': ['common-mode gain', 'cm gain', 'common mode gain'], '18': ['differential-mode gain', 'dm gain', 'differential mode gain', 'differential gain'], '19': ['output balance', 'output balancing', 'balance'], '20': ['cmfb loop stability', 'cmfb stability', 'common mode feedback stability'], '21': ['ugbw', 'unity gain bandwidth', 'unity gain frequency'], '22': ['current', 'supply current', 'bias current', 'operating current', 'i(vdd)', 'i(vdd)', 'i_vdd'], '23': ['dc output voltage', 'dc output', 'output voltage', 'vout'], '24': ['line regulation', 'supply regulation', 'line reg', 'line regulation (v/v)', 'line regulation percent'], '25': ['load regulation', 'load reg', 'load regulation (v/v)', 'load regulation percent'], '26': ['temperature coefficient', 'tc', 'temperature drift', 'temp coefficient'], '27': ['startup behavior', 'startup', 'startup time', 'initialization behavior'], '28': ['current matching', 'current mismatch', 'matching current', 'source sink matching'], '29': ['output ripple', 'ripple', 'output voltage ripple', 'ripple voltage'], '30': ['voltage compliance range', 'compliance range', 'voltage compliance', 'compliance voltage']}, 'list_targets_to_min': ['input_total_noise', 'output_total_noise', 'settle_time', 'current', 'dc_output_voltage', 'line_regulation', 'load_regulation', 'temperature_coefficient', 'startup_behavior', 'current_matching', 'output_ripple', 'area']}
    spec_id_unified = local_config.spec_id_unified
    specifications_table = spec_id_unified["specifications"]
    # print("###spec_id_json = ", spec_id_json)
    # Dynamically generate your minimization list on the fly from RAM
    spec_id_table = {int(k): v["target_id"] for k, v in specifications_table.items()}
        

    # spec_id_table = spec_id_json["table_specs_id"]
    print("###spec_id_table = ", spec_id_table)
    agent_utils.update_tables(struc_update_table, specifications_table,spec_tables_path = None)

see_tables()
