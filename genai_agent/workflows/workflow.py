"""Workflow orchestration for netlist generation, simulation debugging, and spec contract updates."""

import os
import shutil
import sys

from genai_agent.data import local_config
from genai_agent.workflows import compress_err_info_agent
from genai_agent.workflows import make_netlist_agent
from genai_agent.workflows import make_prompt_contract_agent
from genai_agent.workflows import make_pycalculation_agent
from genai_agent.workflows import update_spec_table_agent
from genai_agent.workflows.debug_agent import debug_agent_flow
from ngspice_interface import dut_testbench
from utils import agent_utils
from utils import file_utils
from utils import gen_utils
from utils import sim_utils
from utils import user_interation_utils


def sim_debug_measure_loop(
    netlist,
    spec_sims,
    cir_num,
    path_output_num,
    is_differential_output,
    dc_vout_target,
    has_input=True,
    is_CMFB=False,
    general_rules=None,
    category_debug_rules=None,
    trimmed_spec_table=None,
    metrics_run_id=None,
    metrics_mode=None,
):
    """Run SPICE simulation, debug failures, and measure the resulting netlist."""
    counter = 0
    debug_history = []

    while True:
        old_netlist = netlist
        sim_output = sim_utils.run_ngspice_direct(netlist)
        print("##### sim_output =", sim_output)

        original_msg = sim_output["message"]
        sim_output["message"] = gen_utils.reduce_duplicate_str(original_msg)
        print("##### reduced_message =", sim_output["message"])

        is_sim_success = sim_output["success"]
        if not agent_utils.check_current_simulation(spec_sims):
            is_sim_success = False
            sim_output["message"] = (
                "Mandatory VDD Current simulation (.op) not found. Original message: "
                + sim_output["message"]
            )

        if is_sim_success:
            struct_path_id = gen_utils.make_path_id(spec_sims, path_output_num)
            print(f"##### path_id_{cir_num} =", struct_path_id)

            file_utils.save_dict_to_json(struct_path_id, path_output_num + "struct_path_id.json")
            file_utils.save_dict_to_json(
                {"is_differential": is_differential_output, "has_input": has_input},
                path_output_num + "cir_info.json",
            )
            print("Simulation successful and output files verified!")

            netlist_path = path_output_num + "final_netlist.cir"
            with open(netlist_path, "w", encoding="utf-8") as f:
                f.write(netlist)

            file_utils.save_error_info(
                path_output_num,
                cir_num,
                counter,
                debug_history,
                "success",
                is_CMFB,
                is_differential_output,
                has_input,
            )

            dut = dut_testbench.DUT(
                is_differential=is_differential_output,
                has_input=has_input,
                dc_vout_target=dc_vout_target,
                netlist_path=netlist_path,
            )
            dut.circuit_name = cir_num
            measurement_results = dut.measure_metrics(struct_path_id, is_init=False)

            for mr in measurement_results:
                print("Measurement results:", mr)

            return measurement_results, struct_path_id, counter, debug_history

        print(f"================== bug found, iteration {counter} ========")
        formatted_history_input = ""
        for h in debug_history:
            formatted_history_input += (
                f"### Iteration {h['iteration']}\n"
                f"- **SPICE Error:** {h['error']}\n"
                f"- **Analysis:** {h['analysis']}\n"
                f"- **Fix Plan:** {h['fix_plan']}\n"
                f"- **Fix Applied:** {h['fix']}\n"
                f"- **Differences:** {h['diff']}\n"
            )

        formatted_history_input += (
            f"### Current Iteration {counter}\n- **SPICE Error:** {sim_output['message']}"
        )
        print(formatted_history_input)

        gen_utils.test_delay(30 * (counter + 1), "debug")

        struct_debug = debug_agent_flow(
            netlist,
            formatted_history_input,
            trimmed_spec_table,
            spec_sims,
            general_rules,
            category_debug_rules,
            metrics_run_id=metrics_run_id,
            metrics_circuit_name=str(cir_num),
            metrics_mode=metrics_mode,
        )

        file_utils.save_dict_to_json(
            struct_debug.model_dump(),
            local_config.path_output + f"debug_struct_{counter}.json",
        )

        netlist = struct_debug.netlist
        spec_sims = struct_debug.spec_sims
        new_fix_info = struct_debug.fix_info
        analysis = struct_debug.bug_analysis
        fix_plan = struct_debug.fix_plan

        diff_nl = gen_utils.get_netlist_diff(old_netlist, netlist)
        debug_history.append(
            {
                "iteration": counter,
                "error": sim_output["message"],
                "analysis": analysis,
                "fix_plan": fix_plan,
                "fix": new_fix_info,
                "diff": diff_nl,
            }
        )

        counter += 1
        if counter > 5:
            file_utils.save_error_info(
                path_output_num,
                cir_num,
                counter,
                debug_history,
                "failed",
                is_CMFB,
                is_differential_output,
                has_input,
            )
            raise RuntimeError("Too many iterations in debug-sim loop. Something might be wrong.")


def generate_netlist(
    cir_num,
    path_output_num,
    netlist,
    has_input,
    trimmed_spec_name_table,
    is_diff=None,
    category_num=None,
    general_rules=None,
    cat_json=None,
    category_gen_rules=None,
    category_debug_rules=None,
    contracts=None,
    metrics_run_id=None,
    metrics_mode=None,
):
    """Build a candidate netlist, run simulation, debug failures, and return measurement data."""
    print("generating netlist...")

    if category_num is None:
        raise ValueError("Category number is required.")

    struc = make_netlist_agent.make_netlist_agent_flow(
        netlist=netlist,
        category_json=cat_json,
        category_num=category_num,
        cir_num=cir_num,
        trimmed_spec_name_table=trimmed_spec_name_table,
        is_diff=is_diff,
        general_rules=general_rules,
        category_gen_rules=category_gen_rules,
        contracts=contracts,
        has_input=has_input,
        metrics_run_id=metrics_run_id,
        metrics_mode=metrics_mode,
    )

    target_dc_vout = getattr(struc, "target_dc_vout", None)
    if target_dc_vout is None:
        print("Target DC output voltage is not specified. Using default value of 0.6V.")
        target_dc_vout = 0.6

    target_dc_vout = user_interation_utils.user_modify_input(
        "Target DC Output Voltage", target_dc_vout
    )

    netlist = struc.netlist
    netlist = gen_utils.ensure_data_format_settings(netlist)
    netlist = gen_utils.modify_ac_range_1T(netlist)

    spec_sims = struc.spec_sims
    is_differential_output = struc.is_diff
    is_CMFB = struc.is_CMFB

    # Debug-output summary for workflow tracing
    print("== spec_sims", spec_sims)
    print("#### sim_netlist =", netlist)
    print("#### is_differential_output =", is_differential_output)
    print("#### is_CMFB =", is_CMFB)

    results_original, struct_path_id, counter, debug_history = sim_debug_measure_loop(
        netlist,
        spec_sims,
        cir_num,
        path_output_num,
        is_differential_output,
        target_dc_vout,
        has_input,
        is_CMFB,
        general_rules=general_rules,
        category_debug_rules=category_debug_rules,
        trimmed_spec_table=trimmed_spec_name_table,
        metrics_run_id=metrics_run_id,
        metrics_mode=metrics_mode,
    )

    if counter > 0:
        gen_utils.test_delay(30 * counter, "compress")
        compress_err_info_agent.compress_agent_flow(
            debug_history,
            general_rules,
            category_num,
            metrics_run_id=metrics_run_id,
            metrics_circuit_name=str(cir_num),
            metrics_mode=metrics_mode,
        )

    path_netlist = path_output_num + "final_netlist.cir"
    data_for_dut_yaml = (is_differential_output, has_input, target_dc_vout)
    return results_original, struct_path_id, path_netlist, spec_sims, data_for_dut_yaml



def prepare_new_type(cat_prompt_path, category_json, spec_tables_path, spec_id_unified, metrics_run_id=None, metrics_circuit_name=None, metrics_mode=None):
    """Create or refresh the specification contract table for the current category."""
    backup_spec_table_path = os.path.join(
        os.getcwd(),
        "genai_agent",
        "data",
        "spec_tables",
        "backup",
        "spec_tables_unified.json",
    )
    shutil.copy(spec_tables_path, backup_spec_table_path)

    specifications_table = spec_id_unified["specifications"]
    spec_id_table = {int(k): v["target_id"] for k, v in specifications_table.items()}

    struct_create_prompt = make_prompt_contract_agent.make_prompt_spec_table_contract_agent_flow(
        category_json,
        spec_id_table,
        metrics_run_id=metrics_run_id,
        metrics_circuit_name=metrics_circuit_name,
        metrics_mode=metrics_mode,
    )
    file_utils.save_str_to_file(struct_create_prompt.prompt, cat_prompt_path)
    if not os.path.isfile(cat_prompt_path):
        print("Warning: prompt file was not created:", cat_prompt_path)

    list_spec_contracts = struct_create_prompt.missing_specifications_contract
    missing_specs = [spec.spec_name for spec in list_spec_contracts]
    impossible_specs = struct_create_prompt.impossible_specifications
    valid_contracts = [
        spec for spec in list_spec_contracts if spec.spec_name not in impossible_specs
    ]

    print("#### missing_specs =", missing_specs)
    print("#### impossible_specs =", impossible_specs)
    print("#### valid_contracts =", valid_contracts)

    gen_utils.test_delay(30, "update table")
    struc_update_table = update_spec_table_agent.update_table_agent_flow(
        missing_specs,
        metrics_run_id=metrics_run_id,
        metrics_circuit_name=metrics_circuit_name,
        metrics_mode=metrics_mode,
    )

    updated_spec_id_unified, affected_ids = agent_utils.update_tables(
        struc_update_table,
        specifications_table,
        spec_tables_path,
        valid_contracts,
    )
    print("## new ids ##\naffected_ids =", affected_ids)

    make_pycal(
        affected_ids,
        updated_spec_id_unified,
        category_json,
        metrics_run_id=metrics_run_id,
        metrics_circuit_name=metrics_circuit_name,
        metrics_mode=metrics_mode,
    )
    return updated_spec_id_unified, valid_contracts


def make_pycal(affected_ids, updated_spec_id_unified, category_json, metrics_run_id=None, metrics_circuit_name=None, metrics_mode=None):
    """Save calculation helper plugins for a changed spec contract set."""
    specifications_table = updated_spec_id_unified["specifications"]

    if affected_ids is None:
        affected_set = set()
    elif isinstance(affected_ids, (list, tuple, set)):
        affected_set = set(str(x) for x in affected_ids)
    else:
        affected_set = {str(affected_ids)}

    filtered_contracts = {}
    for k, v in specifications_table.items():
        if k in affected_set:
            filtered_contracts[k] = v["contract"]
            continue
        try:
            if str(v.get("target_id")) in affected_set:
                filtered_contracts[k] = v["contract"]
        except Exception:
            continue

    print("#### filtered_contracts =", filtered_contracts)
    print("#### category_json =", category_json)

    gen_utils.test_delay(30, "make pycal")
    struc = make_pycalculation_agent.make_pycalculation_agent_flow(
        filtered_contracts,
        category_json,
        metrics_run_id=metrics_run_id,
        metrics_circuit_name=metrics_circuit_name,
        metrics_mode=metrics_mode,
    )
    print("## make_calculation_rule_struct =", struc)

    for plugin in struc.plugins:
        function_file_path = f"./utils/pycal_utils/{plugin.function_name}.py"
        file_utils.save_str_to_file(content=plugin.python_code, path=function_file_path)
        print(f"[Saved pycal plugin]: {function_file_path}")

    return filtered_contracts
