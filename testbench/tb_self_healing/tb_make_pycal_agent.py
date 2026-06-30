import importlib.util
import numpy as np
import sys
sys.path.append('.')
from genai_agent.workflows import make_pycalculation_agent
from utils import file_utils
from genai_agent.data.response_schema import SinglePluginFunction 
def tb_make_pycal_agent():
    cat_json = {'category': 'Oscillators and Voltage-Controlled Oscillators (VCOs)', 'required_specs': ['Oscillation Frequency', 'Tuning Range & Gain (for VCOs)', 'Phase Noise', 'Output Swing / Amplitude', 'Power Consumption']}
    filtered_contracts =  {'31': {'sim_type': 'TRAN', 'csv_filenames': 'tran_osc_freq.csv', 'expected_columns': 2, 'python_function_name': 'get_oscillation_frequency'}, '32': {'sim_type': 'TRAN', 'csv_filename': 'tran_tuning.csv', 'expected_columns': 3, 'python_function_name': 'get_tuning_range_and_gain'}}

    make_pycalculation_agent.make_pycalculation_agent_flow(filtered_contracts, cat_json)


def tb_save():
    plugins=[SinglePluginFunction(function_name='calc_spec_31', python_code='def calc_spec_31(raw_data):\n    import numpy as np\n    if raw_data is None or len(raw_data) < 2:\n        return 0.0\n    time = raw_data[:, 0]\n    voltage = raw_data[:, 1]\n    v_ac = voltage - np.mean(voltage)\n    zero_crossings = np.where(np.diff(np.sign(v_ac)) > 0)[0]\n    if len(zero_crossings) < 2:\n        return 0.0\n    t_crossings = []\n    for idx in zero_crossings:\n        t1, t2 = time[idx], time[idx+1]\n        v1, v2 = v_ac[idx], v_ac[idx+1]\n        if v2 != v1:\n            t_cross = t1 - v1 * (t2 - t1) / (v2 - v1)\n            t_crossings.append(t_cross)\n    periods = np.diff(t_crossings)\n    if len(periods) == 0:\n        return 0.0\n    mean_period = np.mean(periods)\n    if mean_period == 0:\n        return 0.0\n    return float(1.0 / mean_period)'), SinglePluginFunction(function_name='calc_spec_32', python_code='def calc_spec_32(raw_data):\n    import numpy as np\n    if raw_data is None or len(raw_data) < 2:\n        return 0.0\n    num_rows = raw_data.shape[0]\n    unique_v = np.unique(raw_data[:, 0])\n    if len(unique_v) == num_rows and num_rows >= 2:\n        freqs = raw_data[:, 1]\n        tuning_range = np.max(freqs) - np.min(freqs)\n        return float(tuning_range)\n    v_ctrls = unique_v\n    if len(v_ctrls) < 2:\n        return 0.0\n    frequencies = []\n    for v in v_ctrls:\n        mask = np.isclose(raw_data[:, 0], v)\n        data_v = raw_data[mask]\n        if len(data_v) < 2:\n            continue\n        time = data_v[:, 1]\n        voltage = data_v[:, 2]\n        v_ac = voltage - np.mean(voltage)\n        zero_crossings = np.where(np.diff(np.sign(v_ac)) > 0)[0]\n        if len(zero_crossings) >= 2:\n            t_crossings = []\n            for idx in zero_crossings:\n                t1, t2 = time[idx], time[idx+1]\n                v1, v2 = v_ac[idx], v_ac[idx+1]\n                if v2 != v1:\n                    t_cross = t1 - v1 * (t2 - t1) / (v2 - v1)\n                    t_crossings.append(t_cross)\n            periods = np.diff(t_crossings)\n            if len(periods) > 0:\n                frequencies.append(1.0 / np.mean(periods))\n    if len(frequencies) < 2:\n        return 0.0\n    tuning_range = np.max(frequencies) - np.min(frequencies)\n    return float(tuning_range)')]
    for plugin in plugins:
        func_name = plugin.function_name
        function_file_path = f"./utils/pycal_utils/{func_name}.py"
        # PERFECT USE CASE FOR YOUR UTILITY METHOD:
        file_utils.save_str_to_file(content=plugin.python_code, path=function_file_path)
        tb_is_new_func_there(function_file_path, func_name)
        print(f"[Healed Plugin saved successfully]: {function_file_path}")

def tb_is_new_func_there(function_file_path, func_name):
    spec = importlib.util.spec_from_file_location(func_name, function_file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    func_to_run = getattr(module, func_name)
    result = float(func_to_run(None))
    print(result)
# tb_make_pycal_agent()
tb_save()

