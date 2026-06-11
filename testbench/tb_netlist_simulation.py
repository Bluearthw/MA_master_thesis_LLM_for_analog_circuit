import sys
sys.path.append('.')
from genai_agent.data import local_config
from genai_agent.data import saved_netlist
from utils import gen_utils

def test_run_ngspice_direct(nl = ""):
    # Write the netlist to a temporary file
    gen_utils.pyspice_op_sim_simple(nl)
    print("===direct::")
    success = gen_utils.run_ngspice_direct(nl)
    print("===success::", success["success"])
    print("===success::", success["message"])

def test_run_ngspice_direct_from_final_netlist(num = 4):
    path_nl = local_config.path_output +  f"{num}/final_netlist.cir"
    netlist = gen_utils.get_file_to_str(path_nl)
    # utils.delete_all_files_skip_dir(local_config.path_output) # delete all previous output to avoid confusion
    
    success = gen_utils.run_ngspice_direct(netlist, False, path_nl) # will not overwrite temp_netlist
    print("==netlist",netlist)
    if success["success"]:
        print("Simulation successful!")
    else:
        print("Simulation failed with message:", success["message"])

def test_run_ngspice_direct_from_temp():
    path_nl = local_config.path_output +  f"temp_circuit.cir"
    netlist = gen_utils.get_file_to_str(path_nl)
    # utils.delete_all_files_skip_dir(local_config.path_output) # delete all previous output to avoid confusion
    
    success = gen_utils.run_ngspice_direct(netlist, False, path_nl) # will not overwrite temp_netlist
    print("==netlist",netlist)
    if success["success"]:
        print("Simulation successful!")
    else:
        print("Simulation failed with message:", success["message"])


# test_run_ngspice_direct(saved_netlist.nl_182_diff_with_cmfb_before_cmfb_agent)
# test_run_ngspice_direct(local_config.nl_2_stage_opamp)
# test_run_ngspice_direct(local_config.nl_feb25)
# test_run_ngspice_direct(saved_netlist.nl_timeout)
# test_run_ngspice_direct(saved_netlist.nl_april_sim_failed_warning)
# test_run_ngspice_direct(saved_netlist.nl_155_failed)
test_run_ngspice_direct(saved_netlist.nl_test_noise_spectrum_failed)

# test_run_ngspice_direct_from_final_netlist(155)
# test_run_ngspice_direct_from_final_netlist(9)
# test_run_ngspice_direct_from_final_netlist(439)
# test_run_ngspice_direct_from_temp()
"""
==netlist in debug agent
 * title line
.param VDD_VAL=1.2
.param wn0=0.5u
.param ln0=90n
.param mn0=1
.param r0=1k
.param c0=3p
.param trf=0.5u
.param period=10u
.include "genai_agent/data/p045_TT.sp"
mn0 VDD VDD VOUT1 VSS nmos w=wn0 l=ln0 m=mn0
R0 VOUT1 VSS {r0}
C0 VOUT1 VSS {c0}
iload VOUT1 VSS dc 0
vdd VDD 0 dc=VDD_VAL
vss VSS 0 dc=0
.control
option numdgt=7
set temp=25
set units=degrees
set wr_vecnames
op
wrdata ./genai_agent/output/6/dc_output.csv v(VOUT1)
wrdata ./genai_agent/output/6/dc_current.csv i(vdd)
dc vdd 0 1.2 0.01
wrdata ./genai_agent/output/6/dc_line_reg.csv v(VOUT1)
dc iload 0 1m 10u
wrdata ./genai_agent/output/6/dc_load_reg.csv v(VOUT1)
dc temp -40 125 1
wrdata ./genai_agent/output/6/dc_tc.csv v(VOUT1)
alter vdd ac=1.0
ac dec 10 1 1T
wrdata ./genai_agent/output/6/ac_psrr.csv v(VOUT1)
noise v(VOUT1) vdd dec 10 1 1T
wrdata ./genai_agent/output/6/noise.csv inoise_total
alter vdd pulse(0 1.2 0.5u 0.5u 0.5u 5u 10u)
tran 0.1u 20u
wrdata ./genai_agent/output/6/tran_startup.csv v(VOUT1)
.endc
.end"""

"""
==netlist after debug * fixed netlist
.param VDD_VAL=1.2
.param wn0=0.5u
.param ln0=90n
.param mn0=1
.param r0=1k
.param c0=3p
.param trf=0.5u
.param period=10u
.include "genai_agent/data/p045_TT.sp"
mn0 VDD VDD VOUT1 VSS nmos w=wn0 l=ln0 m=mn0
R0 VOUT1 VSS {r0}
C0 VOUT1 VSS {c0}
iload VOUT1 VSS dc 0
vdd VDD 0 dc=VDD_VAL ac=1.0 pulse(0 1.2 0.5u 0.5u 0.5u 5u 10u)
vss VSS 0 dc=0
.control
option numdgt=7
set temp=25
set units=degrees
set wr_vecnames
op
wrdata ./genai_agent/output/6/dc_op.csv v(VOUT1) i(vdd)
dc vdd 0 1.2 0.01
wrdata ./genai_agent/output/6/dc_line_reg.csv v(VOUT1)
dc iload 0 1m 10u
wrdata ./genai_agent/output/6/dc_load_reg.csv v(VOUT1)
dc temp -40 125 1
wrdata ./genai_agent/output/6/dc_tc.csv v(VOUT1)
ac dec 10 1 1T
wrdata ./genai_agent/output/6/ac_psrr.csv v(VOUT1)
noise v(VOUT1) vdd dec 10 1 1T
wrdata ./genai_agent/output/6/noise.csv inoise_total
tran 0.1u 20u
wrdata ./genai_agent/output/6/tran_startup.csv v(VOUT1)
.endc
.end"""