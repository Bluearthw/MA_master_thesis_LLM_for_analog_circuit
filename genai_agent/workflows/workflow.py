from genai_agent.data import local_config
from utils import gen_utils 
from utils import file_utils 
from utils import sim_utils
from utils import user_interation_utils
from ngspice_interface import dut_testbench
from genai_agent.workflows.debug_agent import debug_agent_flow
from genai_agent.workflows import make_netlist_agent
from genai_agent.workflows import compress_err_info_agent
def sim_debug_measure_loop(netlist, spec_sims, cir_num, path_output_num, is_differential_output, target_dc_vout, has_input = True, is_CMFB = False, general_rules = None):
    counter = 0
    debug_history = []
    
    while True:
        old_netlist = netlist
        sim_output = sim_utils.run_ngspice_direct(netlist)
        print("=====sim output", sim_output)
        if sim_output["success"]: 
            # check files
            # gather all generated file paths; use a set to ensure uniqueness
            struct_path_id = gen_utils.make_path_id(spec_sims, path_output_num)
            print(f"===  path_id_{cir_num} = ", struct_path_id)
            dict_to_save =  struct_path_id
                    
            dict_to_save2 = {"is_differential": is_differential_output,
                    "has_input": has_input}
            file_utils.save_dict_to_json(dict_to_save, path_output_num + "struct_path_id.json")
            file_utils.save_dict_to_json(dict_to_save2, path_output_num + "cir_info.json")
            print("Simulation successful and output files verified!")
            # save the netlist
            netlist_path = path_output_num + "final_netlist.cir"
            with open(netlist_path, "w") as f:
                f.write(netlist)
            file_utils.save_error_info(path_output_num, cir_num, counter, debug_history, "success", is_CMFB, is_differential_output, has_input)
            # maybe another loop here due to possible error in DUT
            measurement_results = dut_testbench.DUT(is_differential=is_differential_output, has_input=has_input, dc_vout_target=target_dc_vout, netlist_path=netlist_path).measure_metrics(struct_path_id, is_init = False) # how to convert is_differential_output
            for mr in measurement_results:
                print("Measurement results:", mr)
            
            return measurement_results, struct_path_id, counter, debug_history
        else:
            print(f"==================bug found!!!!======={counter}===============")

            formatted_history_input = ""
            for h in debug_history:
                formatted_history_input += f"### Iteration {h['iteration']}\n- **SPICE Error:** {h['error']}\n- **Analysis:** {h['analysis']}\n- **Fix Plan:** {h['fix_plan']}\n- **Fix Applied:** {h['fix']}\n- **Differences:** {h['diff']}\n"
            
            # Append the brand new error to the prompt input
            formatted_history_input += f"### Current Iteration {counter}\n- **SPICE Error:** {sim_output['message']}"
            
            print(formatted_history_input)
            gen_utils.test_delay(30*(counter + 1), "debug")  
            
            # 2. Feed the clean, non-compounding history to the debug agent
            struct_debug = debug_agent_flow(netlist, formatted_history_input, cir_num, spec_sims, general_rules)
            file_utils.save_dict_to_json(struct_debug, local_config.path_output + f"debug_struct_{counter}.json")
            netlist = struct_debug.netlist
            spec_sims = struct_debug.spec_sims
            new_fix_info = struct_debug.fix_info
            analysis = struct_debug.bug_analysis
            fix_plan = struct_debug.fix_plan

            diff_nl = gen_utils.get_netlist_diff(old_netlist, netlist)
            # 3. Save this iteration's clean data into our history tracking object
            debug_history.append({
                "iteration": counter,
                "error": sim_output['message'],
                "analysis": analysis,
                "fix_plan": fix_plan,
                "fix": new_fix_info,
                "diff": diff_nl
            })

        counter += 1
        if counter > 5:
            file_utils.save_error_info(path_output_num, cir_num, counter, debug_history, "failed", is_CMFB, is_differential_output, has_input)
            raise RuntimeError("Too many iterations in debug-sim loop. Something might be wrong.")


def generate_netlist(cir_num, path_output_num, category_str, netlist, has_input, trimmed_spec_table,  is_diff=None, category_num=None, general_rules=None):
    """Generic test-maker that invokes a workflow-local `add_sim_agent` to prepare the netlist,
    then runs the sim-debug-measure loop.

    Parameters:
        - add_sim_agent: callable provided by the workflow (signature varies slightly).
        - cir_num, path_output_num, category_str, netlist, has_input, trimmed_spec_table: workflow params
        - is_diff_arg: optional extra argument forwarded to `add_sim_agent`

    Returns: (combined_results, struct_path_id, path_netlist, spec_sims, data_for_dut_yaml)
    """
    # If a category number is provided, use the central netlist builder
    if category_num is not None:
        struc = make_netlist_agent.netlist_builder(netlist=netlist, category=category_str, category_num=category_num, cir_num=cir_num, trimmed_spec_table=trimmed_spec_table, is_diff=is_diff, general_rules=general_rules)
    else:
        raise ValueError("Category number is required.")

    target_dc_vout = getattr(struc, 'target_dc_vout', None)
    if target_dc_vout is None: # not needed since there it user input
        print("Target DC output voltage is not specified. Using default value of 0.6V.")
        target_dc_vout = 0.6
    # Allow the user to override target interactively (non-blocking helper may be used)
    target_dc_vout = user_interation_utils.user_modify_input("Target DC Output Voltage", target_dc_vout)

    netlist = struc.netlist

    netlist = gen_utils.ensure_data_format_settings(netlist)
    netlist = gen_utils.modify_ac_range_1T(netlist)
        

    spec_sims = struc.spec_sims
    is_differential_output = struc.is_diff
    is_CMFB = struc.is_CMFB
    ####################
    for spec_sim in spec_sims:
        print("==spec_sims", spec_sim)
    print("======sim netlist = ")
    print(netlist)
    print(is_differential_output)
    print("is CMFB:", is_CMFB)
    ####################

    # Run sim-debug-measure loop
    results_original, struct_path_id, counter, debug_history = sim_debug_measure_loop(netlist, spec_sims, cir_num, path_output_num, is_differential_output, target_dc_vout, has_input, is_CMFB, general_rules=general_rules)
    # if debug, let's see compress
    if counter > 0:
        gen_utils.test_delay(30*(counter + 1), "compress")  
        compress_err_info_agent.compress_agent_flow(debug_history, general_rules)
    
    path_netlist = path_output_num + "final_netlist.cir"
    data_for_dut_yaml = (is_differential_output, has_input, target_dc_vout)

    return results_original, struct_path_id, path_netlist, spec_sims, data_for_dut_yaml
