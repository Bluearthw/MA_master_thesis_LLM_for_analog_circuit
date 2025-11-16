
from google.adk.agents import LlmAgent

import PySpice.Logging.Logging as Logging

from PySpice.Spice.NgSpice.Shared import NgSpiceShared
import matplotlib.pyplot as plt
import numpy as np

GEMINI_MODEL = "gemini-2.0-flash"

# def runSpice(circuit: str) -> dict:
def runSpice(circuit) -> dict:
    logger = Logging.setup_logging()
    ngspice = NgSpiceShared.new_instance()

    # print(ngspice.exec_command('version -f'))
    # print(ngspice.exec_command('print all'))
    # print(ngspice.exec_command('devhelp'))
    # print(ngspice.exec_command('devhelp resistor'))

    circuit = '''
    .title Voltage Multiplier

    .SUBCKT 1N4148 1 2
    *
    R1 1 2 5.827E+9
    D1 1 2 1N4148
    *
    .MODEL 1N4148 D
    + IS = 4.352E-9
    + N = 1.906
    + BV = 110
    + IBV = 0.0001
    + RS = 0.6458
    + CJO = 7.048E-13
    + VJ = 0.869
    + M = 0.03
    + FC = 0.5
    + TT = 3.48E-9
    .ENDS

    Vinput in 0 DC 0V AC 1V SIN(0V 10V 50Hz 0s 0Hz)
    C0 in 1 1mF
    X0 1 0 1N4148
    C1 0 2 1mF
    X1 2 1 1N4148
    C2 1 3 1mF
    X2 3 2 1N4148
    C3 2 4 1mF
    X3 4 3 1N4148
    C4 3 5 1mF
    X4 5 4 1N4148
    R1 5 6 1MegOhm
    .options TEMP = 25°C
    .options TNOM = 25°C
    .options filetype = binary
    .options NOINIT
    .ic
    .tran 0.0001s 0.4s 0s
    .end
    '''

    ngspice.load_circuit(circuit)
    ngspice.run()

    plot = ngspice.plot(simulation=None, plot_name=ngspice.last_plot)
    data = plot['V(6)']._data
    time = plot['time']._data

    return {"data":data, "time": time}



CIR_file_add_model_agent = LlmAgent(
    name="CIRfileAddModelAgent",
    # https://ai.google.dev/gemini-api/docs/models
    model="gemini-2.5-flash",
    description="Add Model Design to CIR",
    instruction="""
    You are a helpful .cir file Agent for ngspice . 
    
    Based on the previous OPAMP information:{opamp_info}, 
    the example .cir file with simulation (cir_example), 
    and the generated .cir file {CIR_file_without_model}
    
    Remember to add the .model, like the .model part from the cir_example for nmos. 
    For other passive component, it is not needed.
    Otherwise, the NGspice reports an error.
    if generated .cir file use nmos, you can use the following .model, 
    check the above .cir file for the correct definition, it should have the following at the begining:
        .include "D:\1kulStudy\8MA_Thesis\material\PDK\45nm.sp" 
    With this, the transistor used should be nmos or pmos like:
        M0 VDD VDD VOUT1 VSS nmos w=10u L=1u
    Then, run the runSpice tool. The tool will return a dictionary.
    

    Response with a .cir script for NGspice simulator and the result from the tool 
    """,
    
    output_key ="CIR_file_with_model",
    tools=[runSpice],
    #maybe in 1, use current source in the future
    # before_agent_callback=modify_attachment
)