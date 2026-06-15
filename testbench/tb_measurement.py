import os
import sys
import numpy as np
import matplotlib.pyplot as plt
# local import
sys.path.append(".")
from ngspice_interface import dut_testbench
from genai_agent.data import local_config
from utils import gen_utils
from utils import file_utils
path_id_69 =  {18: './genai_agent/output/69/ac_gain.csv', 1: './genai_agent/output/69/ac_gain.csv', 6: './genai_agent/output/69/ac_gain.csv', 3: './genai_agent/output/69/noise.csv', 4: './genai_agent/output/69/tran_SR.csv', 22: './genai_agent/output/69/dc_current.csv', 23: './genai_agent/output/69/dc_current.csv'}
path_id_96 = {18: './genai_agent/output/96/ac_dm.csv', 17: './genai_agent/output/96/ac_cm.csv', 0: './genai_agent/output/96/ac_gain.csv', 1: './genai_agent/output/96/ac_gain.csv', 16: './genai_agent/output/96/ac_gain.csv', 6: './genai_agent/output/96/ac_gain.csv', 3: './genai_agent/output/96/noise.csv', 4: './genai_agent/output/96/tran_sr.csv', 10: './genai_agent/output/96/dc_sweep.csv', 11: './genai_agent/output/96/dc_sweep.csv'}
path_id_182 = {20: './genai_agent/output/182/cmfb_stb.csv'}
path_id_two_stage = {0: '.\\no_backup\\output_files\\ac_TwoStage.csv', 3: '.\\no_backup\\output_files\\noise_TwoStage.csv', 4: '.\\no_backup\\output_files\\tran_TwoStage.csv', 6: '.\\no_backup\\output_files\\ac_TwoStage.csv', 21: '.\\no_backup\\output_files\\ac_TwoStage.csv', 22: '.\\no_backup\\output_files\\dc_TwoStage.csv'}
path_id_439 =  {28: ['./genai_agent/output/439/source_current.csv', './genai_agent/output/439/sink_current.csv'], 29: './genai_agent/output/439/output_ripple.csv', 30: ['./genai_agent/output/439/source_current.csv', './genai_agent/output/439/sink_current.csv']}

#class 6 bandgap
path_id_6 =  {23: './genai_agent/output/6/dc_vref.csv', 22: './genai_agent/output/6/dc_current.csv', 24: './genai_agent/output/6/dc_line_reg.csv', 25: './genai_agent/output/6/dc_load_reg.csv', 26: './genai_agent/output/6/dc_temp_coeff.csv', 2: './genai_agent/output/6/ac_psrr.csv', 27: './genai_agent/output/6/tran_startup.csv', 7: './genai_agent/output/6/noise.csv'}
path_id_641 =  {23: './genai_agent/output/641/dc_vref.csv', 22: './genai_agent/output/641/dc_current.csv', 24: './genai_agent/output/641/dc_line_reg.csv', 25: './genai_agent/output/641/dc_load_reg.csv', 26: './genai_agent/output/641/dc_temp_coeff.csv', 2: './genai_agent/output/641/ac_psrr.csv', 27: './genai_agent/output/641/tran_startup.csv', 7: './genai_agent/output/641/noise.csv'}
path_id_442 =  {23: './genai_agent/output/442/dc_op.csv', 22: './genai_agent/output/442/dc_current.csv', 24: './genai_agent/output/442/dc_line_reg.csv', 25: './genai_agent/output/442/dc_load_reg.csv', 26: './genai_agent/output/442/dc_tc.csv', 2: './genai_agent/output/442/ac_psrr.csv', 27: './genai_agent/output/442/tran_startup.csv', 7: './genai_agent/output/442/noise.csv'}

#class1 SISO
path_id_9_phase = {5: './genai_agent/output/9/ac_gain.csv', 6: './genai_agent/output/9/ac_gain.csv'}
path_id_9_psrr = {0: './genai_agent/output/9/ac_gain.csv', 2: './genai_agent/output/9/ac_psrr.csv'}
path_id_9_current = {0: './genai_agent/output/9/ac_gain.csv', 22: './genai_agent/output/9/dc_current.csv'}
path_id_57 =  {0: './genai_agent/output/57/ac_gain.csv', 1: './genai_agent/output/57/ac_gain.csv', 2: './genai_agent/output/57/psrr.csv', 3: './genai_agent/output/57/noise.csv', 4: './genai_agent/output/57/tran_SR.csv', 5: './genai_agent/output/57/ac_gain.csv', 6: './genai_agent/output/57/ac_gain.csv', 13: './genai_agent/output/57/icmr.csv', 22: './genai_agent/output/57/dc_current.csv', 23: './genai_agent/output/57/icmr.csv'}
#class 40 DODO
path_id_310 =  {18: './genai_agent/output/310/ac_gain.csv', 17: './genai_agent/output/310/cm_gain.csv', 19: './genai_agent/output/310/tran_settle.csv', 20: './genai_agent/output/310/cmfb_stb.csv', 12: './genai_agent/output/310/tran_settle.csv', 22: './genai_agent/output/310/dc_current.csv', 23: './genai_agent/output/310/dc_current.csv'}

#class 7 DISO
path_id_155_2path_cmrr =  {0: './genai_agent/output/155/ac_gain.csv', 6: './genai_agent/output/155/ac_gain.csv', 16: './genai_agent/output/155/ac_gain.csv', 14: ['./genai_agent/output/155/ac_gain.csv', './genai_agent/output/155/ac_cm.csv'], 17: './genai_agent/output/155/ac_cm.csv', 2: './genai_agent/output/155/psrr.csv', 13: './genai_agent/output/155/icmr.csv', 11: './genai_agent/output/155/swing.csv', 4: './genai_agent/output/155/tran_sr.csv', 22: './genai_agent/output/155/current.csv', 23: './genai_agent/output/155/current.csv'}
path_id_155_1path_cmrr =  {0: './genai_agent/output/155/ac_gain.csv', 6: './genai_agent/output/155/ac_gain.csv', 13: './genai_agent/output/155/icmr.csv', 14: './genai_agent/output/155/cmrr.csv', 2: './genai_agent/output/155/psrr.csv', 11: './genai_agent/output/155/swing.csv', 4: './genai_agent/output/155/tran_SR.csv', 22: './genai_agent/output/155/current.csv', 23: './genai_agent/output/155/dc_vout.csv'}
path_id_320 =  {0: './genai_agent/output/320/ac_gain.csv', 2: './genai_agent/output/320/psrr.csv', 4: './genai_agent/output/320/tran_SR.csv', 6: './genai_agent/output/320/ac_gain.csv', 11: './genai_agent/output/320/dc_out_swing.csv', 13: './genai_agent/output/320/dc_icmr.csv', 14: ['./genai_agent/output/320/ac_gain.csv', './genai_agent/output/320/cm_gain.csv'], 16: './genai_agent/output/320/ac_gain.csv', 17: './genai_agent/output/320/cm_gain.csv', 22: './genai_agent/output/320/current.csv', 23: './genai_agent/output/320/dc_vout.csv'}
path_id_333 =  {0: './genai_agent/output/333/ac_gain.csv', 2: './genai_agent/output/333/ac_psrr.csv', 4: './genai_agent/output/333/tran_sr.csv', 6: './genai_agent/output/333/ac_gain.csv', 11: './genai_agent/output/333/dc_swing.csv', 13: './genai_agent/output/333/dc_icmr.csv', 14: ['./genai_agent/output/333/ac_gain.csv', './genai_agent/output/333/ac_cm_gain.csv'], 16: './genai_agent/output/333/ac_gain.csv', 17: './genai_agent/output/333/ac_cm_gain.csv', 22: './genai_agent/output/333/current.csv', 23: './genai_agent/output/333/dc_vout.csv'}
path_id_619 =  {0: './genai_agent/output/619/ac_gain.csv', 2: './genai_agent/output/619/psrr.csv', 4: './genai_agent/output/619/tran_sr.csv', 6: './genai_agent/output/619/ac_gain.csv', 11: './genai_agent/output/619/output_swing.csv', 13: './genai_agent/output/619/icmr.csv', 14: './genai_agent/output/619/cm_gain.csv', 16: './genai_agent/output/619/ac_gain.csv', 22: './genai_agent/output/619/current.csv', 23: './genai_agent/output/619/dc_vout.csv'}
path_id_439 =  {22: './genai_agent/output/439/current.csv', 23: './genai_agent/output/439/op_vout_ref.csv', 28: ['./genai_agent/output/439/source_current.csv', './genai_agent/output/439/sink_current.csv'], 29: './genai_agent/output/439/output_ripple.csv', 30: ['./genai_agent/output/439/source_current.csv', './genai_agent/output/439/sink_current.csv']}

def test_phase_calculation():
    print("--- SPICE Phase Processing Test Bench ---")
    
    # 1. Simulate a signal that rotates multiple times (e.g., a high-order filter)
    # Frequency from 1Hz to 100GHz (log space)
    freqs = np.logspace(0, 11, 10) 
    y = -1 + 2 * np.random.randn(1, 10)
    x = -1 + 2 * np.random.randn(1, 10)
    print(x)
    print(y)
    complex_v = x+1j*y
    wrapped_phase_deg = np.angle(complex_v, deg=True)
    unwrapped_phase_deg = np.unwrap(wrapped_phase_deg, period=360)
    unwrapped_phase_deg_180 = np.unwrap(wrapped_phase_deg, period=180)
    unwrapped_phase_deg_default_period = np.unwrap(wrapped_phase_deg)
    print(wrapped_phase_deg)
    print(unwrapped_phase_deg)
    print(unwrapped_phase_deg_180)
    print(unwrapped_phase_deg_default_period)
    
def test_measurement_spice_result_new(path_id):
    result = utils.measure(path_id)
    print(result)
    # print(result["icmr"][0])

def test_DUT(cir_num, is_differential_output=False, has_input = False, target_dc_vout=0.6, pid=None):
    path_output_num = local_config.path_output + f"{cir_num}/"
    if pid is None:
        path = path_output_num + "struct_path_id.json"
        print("Path:", path)
        p_id = file_utils.get_dict_from_json_with_int_keys(path)
    else:
        p_id = pid
    print("p_id:", p_id)
    dut =dut_testbench.DUT(is_differential=is_differential_output, has_input=has_input, dc_vout_target=target_dc_vout)
    dut.circuit_name = str(cir_num)
    path = path_output_num + "final_netlist.cir"#???
    dut.netlist_path = path
    result = dut.measure_metrics(p_id)
    print(result)
 
def test_DUT_with_yaml():
    project_path = os.getcwd()
    # yaml_path = os.path.join(project_path, 'ngspice_interface', 'files', 'yaml_files', '9.yaml')
    
    yaml_path = os.path.join(project_path, 'ngspice_interface', 'files', 'yaml_files', 'TwoStage.yaml')
    parameters = {
        'mp1': 10,
        'wp1': 5.0e-07,
        'lp1': 100.0e-09,
        'mn1': 10,
        'wn1': 5.0e-07,
        'ln1': 100.0e-09,
        'mp3': 10,
        'wp3': 5.0e-07,
        'lp3': 100.0e-09,
        'mn3': 10,
        'wn3': 5.0e-07,
        'ln3': 100.0e-09,
        'mn4': 10,
        'wn4': 5.0e-07,
        'ln4': 100.0e-09,
        'mn5': 10,
        'wn5': 5.0e-07,
        'ln5': 100.0e-09,
        'cap': 5.0e-12,
        'res': 5.0e+3
    }
    process = "TT"
    temp_pvt = 27
    vdd = 1.2
    dut_tb = dut_testbench.DUT(yaml_path)

    dut_tb.output_files_folder = "./no_backup/output_files"
    dut_tb.random_name = "TwoStage"
    
    new_netlist_path = dut_tb.create_new_netlist(parameters, process, temp_pvt, vdd)
    info = dut_tb.simulate(new_netlist_path)
    dut_tb.random_name = "TwoStage"
    print(f"New netlist created at: {new_netlist_path}")
    print("info:", info)
    print("trf:", dut_tb.trf)
    print("period:", dut_tb.period)
    print("VDD:", dut_tb.VDD)
    # noise, dc gain phm sr ugbw
    path_id_two_stage = {0: '.\\no_backup\\output_files\\ac_TwoStage.csv', 3: '.\\no_backup\\output_files\\noise_TwoStage.csv', 4: '.\\no_backup\\output_files\\tran_TwoStage.csv', 6: '.\\no_backup\\output_files\\ac_TwoStage.csv'}
     
    dut_tb.measure_metrics(path_id_two_stage)

def test_DUT_180_phase_problem(p_id, name):
    dut = dut_testbench.DUT()
    dut.circuit_name = str(name)
    result = dut.measure_metrics(p_id)
    print (result)
    phase_deg = dut.get_phase_response()
    print(phase_deg[-1])
    print(phase_deg[0])
    # plt.figure(figsize=(8, 5))
    # plt.semilogx(dut.freq, phase_deg)
    # plt.title("Phase Response")
    # plt.xlabel("Frequency (Hz)")
    # plt.ylabel("Phase (Degrees)")
    # plt.grid(True, which="both", linestyle="--")
    # plt.axhline(y=-180, color='r', linestyle=':', label='-180° Limit')
    # plt.legend()
    # plt.show()

def test_DUT_ugbw(cir_name):
    dut = dut_testbench.DUT()
    dut.circuit_name = str(cir_name)
    p_id = gen_utils.get_file_to_str(local_config.path_output + f"{cir_name}/struct_path_id.txt")
    print("p_id:", p_id)
    result = dut.measure_metrics(p_id)
    print (result)
    phase_deg = dut.get_phase_response()
    print(phase_deg[-1])
    print(phase_deg[0])
    # plt.figure(figsize=(8, 5))
    # plt.semilogx(dut.freq, phase_deg)
    # plt.title("Phase Response")
    # plt.xlabel("Frequency (Hz)")
    # plt.ylabel("Phase (Degrees)")
    # plt.grid(True, which="both", linestyle="--")
    # plt.axhline(y=-180, color='r', linestyle=':', label='-180° Limit')
    # plt.legend()
    # plt.show()

def test_DUT_psrr_len_problem(p_id, name):
    dut = dut_testbench.DUT()
    dut.circuit_name = str(name)
    result = dut.measure_metrics(p_id)
    print (result)

def test_get_vdd(cir_cum):
    dut = dut_testbench.DUT()
    path = local_config.path_output + f"{cir_cum}/final_netlist.cir"
    # dut.netlist_path = "./no_backup/netlists/TwoStage.cir"
    dut.netlist_path = path
    vdd = dut.get_vdd()
    print(f"VDD: {vdd}")

def test_v_compliance_range(cir_cum= 439, path_id = path_id_439, sim = False):
    if sim:
        gen_utils.run_ngspice_direct_from_final_netlist(cir_cum)
    dut = test_DUT(path_id, cir_cum) 
    sink_path = local_config.path_output + f"{cir_cum}/sink_current.csv"
    source_path = local_config.path_output + f"{cir_cum}/source_current.csv"
    
    # Load and plot the current data
    data_sink = np.genfromtxt(sink_path, autostrip=True, skip_header=1)
    data_source = np.genfromtxt(source_path, autostrip=True, skip_header=1)
    
    v_sweep = data_sink[:, 0]
    i_sink = data_sink[:, 1]
    i_source = data_source[:, 1]
    
    # Create visualization
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # Plot 1: Source and Sink Currents
    ax1.plot(v_sweep, i_source * 1e9, 'b-', linewidth=2, label='Source Current')
    ax1.plot(v_sweep, i_sink * 1e9, 'r-', linewidth=2, label='Sink Current')
    if dut.compliance_range_min_max is not None:
        v_min, v_max = dut.compliance_range_min_max[0], dut.compliance_range_min_max[1]
        ax1.axvline(v_min, color='g', linestyle='--', alpha=0.7, label=f'Compliance Min: {v_min:.3f}V')
        ax1.axvline(v_max, color='orange', linestyle='--', alpha=0.7, label=f'Compliance Max: {v_max:.3f}V')
    ax1.set_xlabel('Output Voltage (V)')
    ax1.set_ylabel('Current (nA)')
    ax1.set_title('Source and Sink Currents vs Output Voltage')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Current Mismatch
    i_avg = (np.abs(i_source) + np.abs(i_sink)) / 2.0
    i_avg = np.where(i_avg == 0, 1e-12, i_avg)
    mismatch = np.abs(i_source - i_sink) / i_avg * 100
    
    ax2.plot(v_sweep, mismatch, 'purple', linewidth=2, label='Current Mismatch (%)')
    ax2.axhline(5.0, color='orange', linestyle='--', alpha=0.5, label='5% Error Threshold')
    if dut.compliance_range_min_max is not None:
        v_min, v_max = dut.compliance_range_min_max[0], dut.compliance_range_min_max[1]
        ax2.axvline(v_min, color='g', linestyle='--', alpha=0.7, label=f'Compliance Min: {v_min:.3f}V')
        ax2.axvline(v_max, color='orange', linestyle='--', alpha=0.7, label=f'Compliance Max: {v_max:.3f}V')
        ax2.fill_betweenx([0, 100], v_min, v_max, alpha=0.2, color='green', label='Compliance Range')
    ax2.set_xlabel('Output Voltage (V)')
    ax2.set_ylabel('Mismatch (%)')
    ax2.set_title('Current Matching Mismatch')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0, 50])
    
    plt.tight_layout()
    plt.savefig(local_config.path_output + f"{cir_cum}/compliance_range_plot.png", dpi=150, bbox_inches='tight')
    plt.show()
    
    # Print compliance information
    if dut.compliance_range_min_max is not None:
        v_min, v_max, idx_min, idx_max = dut.compliance_range_min_max
        compliance_range = v_max - v_min
        print(f"\n=== Voltage Compliance Range ===")
        print(f"Min Voltage: {v_min:.6f} V")
        print(f"Max Voltage: {v_max:.6f} V")
        print(f"Compliance Range: {compliance_range:.6f} V")
        print(f"Current Mismatch at Min: {mismatch[idx_min]:.2f}%")
        print(f"Current Mismatch at Max: {mismatch[idx_max]:.2f}%")
    else:
        print("No valid compliance range found.")

#region test entrance
# test_phase_calculation()
# test_DUT(path_id_6, 6, is_differential_output=False, has_input=False, target_dc_vout=0.6)
# test_DUT(path_id_69, 69, True, True, 0.6) 
# test_DUT(path_id_439, 439) 
# test_DUT(path_id_641, 641) 
# test_DUT(path_id_155_2path_cmrr, 155, has_input=True) 
# test_DUT(path_id_155_1path_cmrr, 155, has_input=True) 
# test_DUT(439, has_input=True,pid=path_id_439) 
# test_DUT_180_phase_problem(path_id_9_phase, 9)
# test_DUT_psrr_len_problem(path_id_9_psrr, 9)
# test_DUT_with_yaml()
# test_DUT(1005, has_input=True, is_differential_output=True)
test_DUT(549)
# test_v_compliance_range(sim = True)
# test_v_compliance_range(sim = False)

# test_get_vdd(439)
#endregion test entrance