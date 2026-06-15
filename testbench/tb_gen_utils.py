import os
import sys
from pprint import pprint

sys.path.append(".")
from utils import gen_utils
from utils import file_utils
from genai_agent.data import local_config
from genai_agent.data import category_numbers
from genai_agent.workflows.compress_err_info_agent import backup_prompts
def test_count_retry_info(cir_nums):
    total, average, zero_retry_count = gen_utils.count_retry_info(cir_nums)
    print(f"Total retries: {total}, Average retries: {average}, Zero retries: {zero_retry_count}")

def test_find_cir_num_without_pattern(nums, port = []):
    dataset_path = "../material/dataset/tb_dataset"

    nums_new = gen_utils.find_cir_num_without_pattern(dataset_path,port,nums)
    print("#old ", len(nums))
    print(nums)
    print("#new ", len(nums_new))
    print(nums_new)

def test_trim_spec_table(category_num):
    print(local_config.path_category_md)
    path_category = local_config.path_category_md + f"{category_num}.md"
    print(path_category)
    # or the cat_num is already known, so just +"4.md"
    category_str = gen_utils.get_file_to_str(path_category)
    new_dict = gen_utils.trim_spec_table(category_str)
    print("old_dict:\n", local_config.table_specs_id)
    print("new_dict:\n", new_dict)

def test_save_load_prompt():
    
    os.makedirs(local_config.path_prompts , exist_ok=True)
    prompt_path = os.path.join(local_config.path_prompts , f"prompt_test.md")

    f_end = "1T"
    general_rules = local_config.general_rules.replace('{f_end}', f_end)
    contents = """You are a......
0. Gain example, the VOUT1 is the output node. Example:* for gain
ac dec 10 1 {f_end}
Vinput aid VSS dc=0.0 ac=1.0 PULSE({{-VHIGH*0.5}}
{general_rules} 
"""
    file_utils.save_str_to_file(contents, prompt_path)
    return prompt_path

def test_get_prompt():
    f_end = "1T"
    prompt_dir = local_config.path_prompts 
    prompt_path = os.path.join(prompt_dir, f"prompt_test.md")
    general_rules = local_config.general_rules.replace('{f_end}', f_end)
    # result = gen_utils.get_file_to_str(prompt_path).replace('{general_rules}', general_rules).replace('{f_end}', f_end)
    # result = gen_utils.get_file_to_str(prompt_path).format(general_rules=general_rules, f_end=f_end)
    result = gen_utils.get_file_to_str(prompt_path).format(general_rules=general_rules,
                                                           f_end=f_end, 
                                                           line_wrdata_path_num="line_wrdata_path_num", 
                                                           netlist="netlist",
                                                           is_diff = "is_diff",
                                                           trimmed_spec_table = "trimmed_spec_table",
                                                           category = "category",
                                                           cir_num = "cir_num"
                                                           )
    print(result)


def test_is_cir_debugged(nums):
    for i in nums:
        if gen_utils.is_cir_debugged(i):
            print(f"Circuit {i} is debugged.")

def test_update_gen_rules_json():
    """Scan the prompts directory and write a single `workflow_prompts.json` file.

    The JSON will map prompt basename (without extension) -> prompt contents.
    This is intended to be run once to build a cache used by workflows/tests.
    """
    prompt_dir = local_config.path_prompts
    os.makedirs(prompt_dir, exist_ok=True)

    out_path = os.path.join(prompt_dir, 'workflow_prompts.json')
    try:
        

        # Write structured JSON with general rules as a list and the prompt map.
        general_rules = local_config.general_rules
        general_rules_list = [line.strip() for line in general_rules.splitlines() if line.strip()]

        payload = {
            "general_rules": general_rules_list,
        }
        file_utils.save_dict_to_json(payload, out_path)
        return out_path
    except Exception as e:
        print(f"update_prompts_json failed: {e}")
        return None
    
def test_reduce_duplicate(duplicate_str):
    reduced =gen_utils.reduce_duplicate(duplicate_str)
    
    print("Original:\n", duplicate_str)
    print("Reduced:\n", reduced)

def test_get_wf_p():
    prompts_path = local_config.path_prompts + "workflow_prompts.json"
    dict = gen_utils.get_dict_from_json(prompts_path)
    general_rules = dict.get('general_rules')
    print(general_rules)

def test_backup_prompt():
    prompts_path = os.path.join(local_config.path_prompts, 'workflow_prompts.json')
    backup_path = backup_prompts(prompts_path)
    if os.path.isfile(backup_path):
        print(f"Prompt backup created successfully: {backup_path}")

def test_ensure_format():
    nl = '* title line\\n*params\\n.param VB1_VAL=0.7\\n.param VB2_VAL=0.7\\n.param VB3_VAL=0.4\\n.param VB4_VAL=1.0\\n.param VB5_VAL=0.8\\n.param VB6_VAL=0.2\\n.param VB7_VAL=0.8\\n.param VB8_VAL=0.4\\n.param VB9_VAL=0.9\\n.param VDD_VAL=1.2\\n.param Cload=1p\\n.param wp26=0.5u lp26=90n mp26=1\\n.param wp25=0.5u lp25=90n mp25=1\\n.param wp24=0.5u lp24=90n mp24=1\\n.param wp23=0.5u lp23=90n mp23=1\\n.param wp14=0.5u lp14=90n mp14=1\\n.param wp13=0.5u lp13=90n mp13=1\\n.param wp12=0.5u lp12=90n mp12=1\\n.param wp9=0.5u lp9=90n mp9=1\\n.param wp6=0.5u lp6=90n mp6=1\\n.param wp5=0.5u lp5=90n mp5=1\\n.param wp4=0.5u lp4=90n mp4=1\\n.param wp3=0.5u lp3=90n mp3=1\\n.param wp2=0.5u lp2=90n mp2=1\\n.param wp1=0.5u lp1=90n mp1=1\\n.param wp0=0.5u lp0=90n mp0=1\\n.param wn34=0.5u ln34=90n mn34=1\\n.param wn33=0.5u ln33=90n mn33=1\\n.param wn32=0.5u ln32=90n mn32=1\\n.param wn31=0.5u ln31=90n mn31=1\\n.param wn30=0.5u ln30=90n mn30=1\\n.param wn29=0.5u ln29=90n mn29=1\\n.param wn28=0.5u ln28=90n mn28=1\\n.param wn27=0.5u ln27=90n mn27=1\\n.param wn22=0.5u ln22=90n mn22=1\\n.param wn21=0.5u ln21=90n mn21=1\\n.param wn20=0.5u ln20=90n mn20=1\\n.param wn19=0.5u ln19=90n mn19=1\\n.param wn18=0.5u ln18=90n mn18=1\\n.param wn17=0.5u ln17=90n mn17=1\\n.param wn16=0.5u ln16=90n mn16=1\\n.param wn15=0.5u ln15=90n mn15=1\\n.param wn11=0.5u ln11=90n mn11=1\\n.param wn10=0.5u ln10=90n mn10=1\\n.param wn8=0.5u ln8=90n mn8=1\\n.param wn7=0.5u ln7=90n mn7=1\\n.param trf=10n\\n.param period=10u\\n.include "genai_agent/data/p045_TT.sp"\\nmp26 net62 VB5 net53 VDD pmos w=wp26 l=lp26 m=mp26\\nmp25 net75 VB5 net29 VDD pmos w=wp25 l=lp25 m=mp25\\nmp24 net53 VB4 VDD VDD pmos w=wp24 l=lp24 m=mp24\\nmp23 net29 VB4 VDD VDD pmos w=wp23 l=lp23 m=mp23\\nmp14 net87 VB2 net58 VDD pmos w=wp14 l=lp14 m=mp14\\nmp13 net28 VB2 net32 VDD pmos w=wp13 l=lp13 m=mp13\\nmp12 net58 VB1 VDD VDD pmos w=wp12 l=lp12 m=mp12\\nmp9 net32 VB1 VDD VDD pmos w=wp9 l=lp9 m=mp9\\nmp6 VOUT1 net87 net89 VDD pmos w=wp6 l=lp6 m=mp6\\nmp5 VOUT2 net28 net23 VDD pmos w=wp5 l=lp5 m=mp5\\nmp4 net89 VB9 VDD VDD pmos w=wp4 l=lp4 m=mp4\\nmp3 net23 VB9 VDD VDD pmos w=wp3 l=lp3 m=mp3\\nmp2 net72 VIN1 net16 VDD pmos w=wp2 l=lp2 m=mp2\\nmp1 net88 VIN2 net16 VDD pmos w=wp1 l=lp1 m=mp1\\nmp0 net16 VB7_gate VDD VDD pmos w=wp0 l=lp0 m=mp0\\nmn34 net62 VB6 VSS VSS nmos w=wn34 l=ln34 m=mn34\\nmn33 net52 VB6 VSS VSS nmos w=wn33 l=ln33 m=mn33\\nmn32 net39 VB6 VSS VSS nmos w=wn32 l=ln32 m=mn32\\nmn31 net75 VB6 VSS VSS nmos w=wn31 l=ln31 m=mn31\\nmn30 net53 net88 net52 VSS nmos w=wn30 l=ln30 m=mn30\\nmn29 net29 VSS net52 VSS nmos w=wn29 l=ln29 m=mn29\\nmn28 net53 VSS net39 VSS nmos w=wn28 l=ln28 m=mn28\\nmn27 net29 net72 net39 VSS nmos w=wn27 l=ln27 m=mn27\\nmn22 net87 VB3 VSS VSS nmos w=wn22 l=ln22 m=mn22\\nmn21 net57 VB3 VSS VSS nmos w=wn21 l=ln21 m=mn21\\nmn20 net42 VB3 VSS VSS nmos w=wn20 l=ln20 m=mn20\\nmn19 net28 VB3 VSS VSS nmos w=wn19 l=ln19 m=mn19\\nmn18 net58 net89 net57 VSS nmos w=wn18 l=ln18 m=mn18\\nmn17 net32 VSS net57 VSS nmos w=wn17 l=ln17 m=mn17\\nmn16 net58 VSS net42 VSS nmos w=wn16 l=ln16 m=mn16\\nmn15 net32 net23 net42 VSS nmos w=wn15 l=ln15 m=mn15\\nmn11 net72 VB8 VSS VSS nmos w=wn11 l=ln11 m=mn11\\nmn10 net88 VB8 VSS VSS nmos w=wn10 l=ln10 m=mn10\\nmn8 VOUT1 net62 net88 VSS nmos w=wn8 l=ln8 m=mn8\\nmn7 VOUT2 net75 net72 VSS nmos w=wn7 l=ln7 m=mn7\\nvdd VDD 0 dc=VDD_VAL\\nvss VSS 0 dc=0\\nvb1 VB1 0 dc=VB1_VAL\\nvb2 VB2 0 dc=VB2_VAL\\nvb3 VB3 0 dc=VB3_VAL\\nvb4 VB4 0 dc=VB4_VAL\\nvb5 VB5 0 dc=VB5_VAL\\nvb6 VB6 0 dc=VB6_VAL\\nvb8 VB8 0 dc=VB8_VAL\\nvb9 VB9 0 dc=VB9_VAL\\nvdm vdm 0 dc 0 ac 1 PULSE(-0.1 0.1 10n {trf} {trf} {0.5*period} {period})\\nvcm vcm 0 dc 0.6 ac 1\\nein1 VIN1 vcm vdm 0 0.5\\nein2 VIN2 vcm vdm 0 -0.5\\nCL1 VOUT1 0 {Cload}\\nCL2 VOUT2 0 {Cload}\\nLloop VB7 VB7_gate 1G\\nCloop VB7_gate loop_inj 1G\\nVi loop_inj 0 dc=0.8 ac=1\\n.control\\noption numdgt=7\\nset temp=25\\nset units=degrees\\nset wr_vecnames\\n* 1 Current and DC VOUT\\nop\\nwrdata ./genai_agent/output/1005/current.csv i(vdd)\\nwrdata ./genai_agent/output/1005/op_dc_vout.csv v(VOUT1)\\n* 2 DM Gain and Output Balance\\nalter @Vi[acmag]=0\\nac dec 10 1 100G\\nwrdata ./genai_agent/output/1005/ac_dm_gain.csv v(VOUT1) v(VOUT2)\\n* 3 CM Gain\\nalter vdm ac=0\\nalter vcm ac=1\\nac dec 10 1 100G\\nwrdata ./genai_agent/output/1005/ac_cm_gain.csv v(VOUT1) v(VOUT2)\\n* 4 PSRR\\nalter vcm ac=0\\nalter @vdd[acmag]=1\\nac dec 10 1 100G\\nwrdata ./genai_agent/output/1005/ac_psrr.csv v(VOUT1) v(VOUT2)\\n* 5 Large Signal Transient for Swing and Settle\\nalter @vdd[acmag]=0\\ntran 10n 20u\\nwrdata ./genai_agent/output/1005/tran_large_signal.csv v(VOUT1) v(VOUT2)\\n* 6 Temperature Coefficient\\ndc temp -40 125 1\\nwrdata ./genai_agent/output/1005/temp_coeff.csv v(VOUT1)\\n* 7 CMFB Stability\\nalter vdm ac=0\\nalter vcm ac=0\\nalter @Vi[acmag]=1\\nac dec 10 1 100G\\nwrdata ./genai_agent/output/1005/cmfb_stb.csv v(VB7) v(VB7_gate)\\n.endc\\n.end'
    print(nl)
    new_nl = gen_utils.ensure_data_format_settings(nl)
    print(new_nl)
charge_pump_nums = [439, 440, 549, 550, 551, 552, 553, 603] # charge pump\
bandgap_nums = category_numbers.num_class_6_without_IIN1
amplifier_nums = category_numbers.num_class_40_samples_tested
# test_count_retry_info(bandgap_nums)

# bandgap_nums_old = category_numbers.num_class_6
# test_find_cir_num_without_pattern(bandgap_nums_old,["IIN1"])


# test_trim_spec_table(1)
# test_save_load_prompt()
# test_get_prompt()
test_is_cir_debugged(charge_pump_nums)

# test_update_gen_rules_json()
# test_reduce_duplicate("")

# test_get_wf_p()

# test_backup_prompt()
# test_ensure_format()