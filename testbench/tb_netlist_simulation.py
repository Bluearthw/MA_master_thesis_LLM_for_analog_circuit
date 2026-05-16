import sys
sys.path.append('.')
from genai_agent import local_config
from genai_agent import saved_netlist
from utils import gen_utils
def test_run_ngspice_direct_from_final_netlist(num = 4):
    netlist = gen_utils.get_file_to_str(local_config.path_output +  f"{num}/final_netlist.cir")
    path_nl = local_config.path_output +  f"{num}/final_netlist.cir"
    # utils.delete_all_files_skip_dir(local_config.path_output) # delete all previous output to avoid confusion
    
    success = gen_utils.run_ngspice_direct(netlist, False,path_nl)
    print("==netlist",netlist)
    if success["success"]:
        print("Simulation successful!")
    else:
        print("Simulation failed with message:", success["message"])

def test_run_ngspice_direct(nl = local_config.nl_2_stage_opamp):
    # Write the netlist to a temporary file
    gen_utils.pyspice_op_sim_simple(nl)
    print("===direct::")
    success = gen_utils.run_ngspice_direct(nl)
    print("===success::", success["success"])
    print("===success::", success["message"])

# test_run_ngspice_direct(saved_netlist.nl_182_diff_with_cmfb_before_cmfb_agent)
# test_run_ngspice_direct(local_config.nl_2_stage_opamp)
# test_run_ngspice_direct(local_config.nl_feb25)
# test_run_ngspice_direct(saved_netlist.nl_timeout)
# test_run_ngspice_direct(saved_netlist.nl_april_sim_failed_warning)
# test_run_ngspice_direct(saved_netlist.nl_155_failed)

# test_run_ngspice_direct_from_final_netlist(155)
# test_run_ngspice_direct_from_final_netlist(9)
test_run_ngspice_direct_from_final_netlist(439)
