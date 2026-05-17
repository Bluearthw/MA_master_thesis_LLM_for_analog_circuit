git add .
git commit -m "bug found. netlist different. test_make_cir_cim() problem
"
git push

## entrance: main.py!!

venv\Scripts\Activate.ps1
# MA_master_thesis_LLM_for_analog_circuit

number of netlists : 894
"amplifier" and "Amplifier"
opamp : 470
SISO_opamps : 334
SISO_opamps without clk Iin Iout : 289
SISO_opamps with only VB,VIN1,VOUT1 and VBn : 171


69, 77 is differential
# RF
    LNA, PA, DA / IGA??
    not RF: 9, 166
467 has L and it is LNA (low nosie) for RF
465 does not have L but it is also RF
456, with IB 
522 works like a bandpass
578 with L, it is PA (power)
643 is a schimtt trigger including amplifier
832 is 3 stages
906 2 stage with feedback
1017 parallel path
# comparator, actually, if there is vin2, it is CMP
with "amplifier" :
    1039
    1041, at line 8

```
workplace
├─ circuit_env.py
├─ forAmpOnly
│  ├─ dataset
│  ├─ main.py
│  ├─ memory_agent
│  │  ├─ agent.py
│  │  └─ __init__.py
│  ├─ OPAMP_agent
│  │  ├─ .env
│  │  ├─ agent.py
│  │  ├─ subagents
│  │  │  ├─ CIRfileAddModelAgent
│  │  │  │  ├─ agent.py
│  │  │  │  ├─ __init__.py
│  │  │  │  └─ __pycache__
│  │  │  ├─ CIRfileAgent
│  │  │  │  ├─ agent.py
│  │  │  │  ├─ __init__.py
│  │  │  │  └─ __pycache__
│  │  │  ├─ DCsimulateAgent
│  │  │  │  ├─ agent.py
│  │  │  │  ├─ __init__.py
│  │  │  │  └─ __pycache__
│  │  │  ├─ OPAMPagent
│  │  │  │  ├─ agent.py
│  │  │  │  ├─ __init__.py
│  │  │  │  └─ __pycache__
│  │  │  ├─ __init__.py
│  │  │  └─ __pycache__
│  │  ├─ tools
│  │  │  ├─ tool_NGspice.py
│  │  │  ├─ __init__.py
│  │  │  └─ __pycache__
│  │  ├─ __init__.py
│  │  └─ __pycache__
│  ├─ simulation_agent
│  │  ├─ .env
│  │  ├─ agent.py
│  │  ├─ __init__.py
│  │  └─ __pycache__
│  └─ utils.py
├─ genai_agent
│  ├─ add_sim_agent.py
│  ├─ before2026_py_files
│  │  ├─ 1simplecall.py
│  │  ├─ 2structureCall.py
│  │  ├─ root_agent_about_tools.py
│  │  ├─ root_agent_before_combine_OP_cload .py
│  │  ├─ root_agent_before_tool.py
│  │  └─ root_agent_LLM_change_circuit.py
│  ├─ CAD_window
│  ├─ debug_agent.py
│  ├─ local_config.py
│  ├─ memory
│  │  ├─ category_numbers.py
│  │  └─ __pycache__
│  ├─ nmosinv.cir
│  ├─ pickup_RF_agent
│  ├─ root_agent.py
│  ├─ root_agent_2026.py
│  ├─ saved_netlist.py
│  ├─ testbench
│  │  └─ tb_SpiceResult_SpiceResultNew
│  ├─ test_functions.py
│  ├─ tools.py
│  ├─ utils.py
│  ├─ workflows
│  │  ├─ cmfb_agent.py
│  │  ├─ type40
│  │  │  └─ root_agent_type40
│  │  ├─ type4_TIA
│  │  │  └─ root_agent_type4
│  │  ├─ type7_DISO
│  │  │  └─ root_agent_type7
│  │  └─ __pycache__
│  ├─ __init__.py
│  └─ __pycache__
├─ how to start.txt
├─ ngspice_file
│  ├─ test1.cir
│  ├─ test1_by_hand.cir
│  ├─ vdiv.cir
│  └─ vdiv.log
├─ ngspice_interface
│  ├─ area_estimation.py
│  ├─ dut_testbench.py
│  ├─ files
│  │  ├─ input_netlists
│  │  │  └─ TwoStage.cir
│  │  ├─ spice_models
│  │  │  ├─ p045_FF.sp
│  │  │  ├─ p045_SS.sp
│  │  │  └─ p045_TT.sp
│  │  └─ yaml_files
│  │     └─ TwoStage.yaml
│  ├─ ngspice_wrapper.py
│  ├─ __init__.py
│  └─ __pycache__
├─ README.md
├─ solutions
│  ├─ 2026-03-23--17-18-45
│  ├─ 2026-03-23--17-21-54
│  └─ 2026-03-23--17-26-20
├─ td3
│  ├─ agent.py
│  ├─ buffer.py
│  ├─ sac_baseline.cpython-39-x86_64-linux-gnu.so
│  ├─ __init__.py
│  └─ __pycache__
├─ td3_runner.py
├─ testNGspiceWithPython
│  ├─ gemini_example.py
│  └─ Pyspice_example.py
├─ utils
│  ├─ plotting.py
│  ├─ save_response.py
│  ├─ saving.py
│  ├─ __pycache__
│  └─ ___init__.py
