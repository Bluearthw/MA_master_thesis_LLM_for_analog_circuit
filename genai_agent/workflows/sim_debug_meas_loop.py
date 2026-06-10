from genai_agent import local_config
from genai_agent.debug_agent import debug_agent_flow
from utils import gen_utils 
from utils import saving 
from ngspice_interface import dut_testbench

def sim_debug_measure_loop(netlist, spec_sims, cir_num, path_output_num, is_differential_output, target_dc_vout, has_input = True, is_CMFB = False):
    
    counter = 0
    fix_info = []
    error_msg = []
    while True:
        sim_output = gen_utils.run_ngspice_direct(netlist)
        print("=====sim output", sim_output)
        if sim_output["success"]: 
            # check files
            # gather all generated file paths; use a set to ensure uniqueness
            struct_path_id = gen_utils.make_path_id(spec_sims, path_output_num)
            print(f"===  path_id_{cir_num} = ", struct_path_id)
            gen_utils.save_dict_to_json(struct_path_id, path_output_num + "struct_path_id.json")
            print("Simulation successful and output files verified!")
            # save the netlist
            netlist_path = path_output_num + "final_netlist.cir"
            with open(netlist_path, "w") as f:
                f.write(netlist)
            saving.save_error_info(path_output_num, cir_num, counter, error_msg, fix_info, "success", is_CMFB)
            measurement_results = dut_testbench.DUT(is_differential=is_differential_output, has_input=has_input, dc_vout_target=target_dc_vout, netlist_path=netlist_path).measure_metrics(struct_path_id, is_init = False) # how to convert is_differential_output
            for mr in measurement_results:
                print("Measurement results:", mr)
            return measurement_results, struct_path_id
        else:
            print(f"==================bug found!!!!======={counter}===============")
            # error_msg.append(f"iteration{counter}:")
            # error_msg.append(sim_output["message"] + "")
            error_msg.append(f"iteration{counter}: {sim_output['message']}")# more efficient
            error_msg_input = "\n".join(error_msg)
            print(error_msg_input)
            print("wait 60s before debug")
            gen_utils.test_delay(30*(counter + 1))  # Wait 10 seconds before retrying
            struct_debug = debug_agent_flow(netlist, error_msg_input, cir_num, spec_sims)
            netlist = struct_debug.netlist
            spec_sims = struct_debug.spec_sims
            new_fix_info = struct_debug.fix_info
            fix_info.append("fixing info:\n" + new_fix_info)
            error_msg.append(f"iteration{counter}, fixing info:\n" + new_fix_info)
        counter += 1
        if counter > 5:
            saving.save_error_info(path_output_num, cir_num, counter, error_msg, fix_info, "failed", is_CMFB)
            raise RuntimeError("Too many iterations in debug-sim loop. Something might be wrong.")
