from google.adk.agents import Agent
from google.adk.tools import google_search
import PySpice.Logging.Logging as Logging

from PySpice.Spice.NgSpice.Shared import NgSpiceShared
import matplotlib.pyplot as plt
import numpy as np
def runSpice(circuit : str) -> dict:
    """
    Runs a SPICE simulation using PySpice/NgSpice and returns the results.

    Args:
        circuit (str): The complete SPICE netlist code (e.g., V1 1 0 5V, R1 1 2 1k).

    Returns:
        dict: A dictionary containing the simulation data vectors (e.g., {'time': [...], 'v(out)': [...]}).
    """
    try:
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
        .tran 1ms 400ms 0s
        .end
        '''

        ngspice.load_circuit(circuit)
        ngspice.run()

        plot = ngspice.plot(simulation=None, plot_name=ngspice.last_plot)
        data = plot['V(6)']._data.tolist()
        time = plot['time']._data.tolist()

        return {"data":data[0:10], "time": time[0:10]}
    except Exception as e:
            # It's helpful to return the error message for the LLM to understand
            return {"error": f"NgSpice simulation failed: {str(e)}"}



root_agent = Agent(
    name="simulation_agent",
    model="gemini-2.0-flash",
    description="NGSpice simulation agent",
    instruction="""
    
    You are a helpful assistant that can use the following tools:
    - runSpice
    The circuit you will pass to the tool is from the user.
    response with some value is enough like the first period or last few samples if it takes too much resource

    """,
    tools=[runSpice],
    # tools=[get_current_time],
    # tools=[google_search, get_current_time], # <--- Doesn't work
)
