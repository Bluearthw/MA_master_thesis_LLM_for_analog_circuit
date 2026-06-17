import sys
sys.path.append('.')
from genai_agent.data.response_schema import Struct_specs_sim 
from utils import agent_utils
from utils import gen_utils
from genai_agent.workflows import compress_err_info_agent
from genai_agent.data import local_config

spec_sims=[Struct_specs_sim(spec='DC Output Voltage', sim_file_name='op_dc_vout.csv', spec_id=23), Struct_specs_sim(spec='Line Regulation', sim_file_name='dc_line_reg.csv', spec_id=24), Struct_specs_sim(spec='Load Regulation', sim_file_name='dc_load_reg.csv', spec_id=25), Struct_specs_sim(spec='Temperature Coefficient (TC)', sim_file_name='dc_temp_coeff.csv', spec_id=26), Struct_specs_sim(spec='Power Supply Rejection Ratio (PSRR)', sim_file_name='ac_psrr.csv', spec_id=2), Struct_specs_sim(spec='Startup Behavior', sim_file_name='tran_startup.csv', spec_id=27), Struct_specs_sim(spec='Output total noise', sim_file_name='noise.csv', spec_id=7), Struct_specs_sim(spec='Current', sim_file_name='op_current.csv', spec_id=22)]

sim_netlist ="""* title line
.param IB1_VAL=0.01
.param r1=1k
.param r0=1k
.param r3=1k
.param cload=10p
.param vdd_val=1.2
.include "genai_agent/data/p045_TT.sp"
Q5 net03 net03 VSS 0 npn
Q4 IB1 net07 VSS 0 npn
Q3 net07 net03 net011 0 npn
Q0 VDD IB1 VOUT1 0 npn
R1 VOUT1 net03 {r1}
R0 net011 VSS {r0}
R3 VOUT1 net07 {r3}
Cload VOUT1 VSS {cload}
ib1 IB1 0 dc=IB1_VAL
vss VSS 0 dc=0
Vdd VDD 0 dc={vdd_val} ac=1 PWL(0 0 10u {vdd_val})
Iload VOUT1 0 dc 0
.control
option numdgt=7
set temp=25
set units=degrees
set wr_vecnames
* DC Output Voltage
op
wrdata ./genai_agent/output/860/op_dc_vout.csv v(VOUT1)
* Current Consumption
wrdata ./genai_agent/output/860/op_current.csv i(vdd)
* Line Regulation
dc vdd 1.0 1.4 0.01
wrdata ./genai_agent/output/860/dc_line_reg.csv v(VOUT1)
* Load Regulation
dc Iload 0 100u 1u
wrdata ./genai_agent/output/860/dc_load_reg.csv v(VOUT1)
* Temperature Coefficient (TC)
dc temp -40 125 5
wrdata ./genai_agent/output/860/dc_temp_coeff.csv v(VOUT1)
* Power Supply Rejection Ratio (PSRR)
ac dec 10 1 1T
wrdata ./genai_agent/output/860/ac_psrr.csv v(VOUT1)
* Startup Behavior
tran 50n 100u
wrdata ./genai_agent/output/860/tran_startup.csv v(VOUT1)
* Output Noise
noise v(VOUT1) Vdd dec 10 1 1T
wrdata ./genai_agent/output/860/noise.csv onoise_total
.endc
.end"""
prompt_dict = agent_utils.get_workflow_prompts_json()# should update for every circuit, in the future, some flag to control
general_rules = "\n".join(prompt_dict.get('general_rules'))
is_diff = False
is_CMFB = False
cir_num = 860
path_output_num = local_config.path_output + f"{cir_num}/"
target_dc_vout = 0.6
has_input =False
from genai_agent.workflows.workflow import sim_debug_measure_loop 
results_original, struct_path_id, counter, debug_history = sim_debug_measure_loop(sim_netlist, spec_sims, cir_num, path_output_num, is_diff, target_dc_vout, has_input, is_CMFB, general_rules=general_rules)

# if debug, let's see compress
if counter > 0:
    gen_utils.test_delay(30*(counter + 1), "compress")  
    compress_err_info_agent.compress_agent_flow(debug_history, general_rules)

path_netlist = path_output_num + "final_netlist.cir"
print(f"Final netlist saved to: {path_netlist}")
data_for_dut_yaml = (is_diff, has_input, target_dc_vout)
print(f"Data for DUT YAML: {data_for_dut_yaml}")

