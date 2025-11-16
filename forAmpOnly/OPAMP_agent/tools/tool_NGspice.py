import PySpice.Logging.Logging as Logging

from PySpice.Spice.NgSpice.Shared import NgSpiceShared
import matplotlib.pyplot as plt
import numpy as np

def runSpice():
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

    # print('Loaded circuit:')
    # print(ngspice.listing())

    # print(ngspice.show('c3'))
    # print(ngspice.showmod('c3'))

    ngspice.run()

    # print('Plots:\n', ngspice.plot_names)
    # print('ressource_usage:\n ',ngspice.ressource_usage())
    # print('status\n', ngspice.status())

    plot = ngspice.plot(simulation=None, plot_name=ngspice.last_plot)

    # ngspice.quit()

    # print("\ntest")
    # print('plot?\n',plot)
    # print(plot['in'])
    """ this works
    data = np.array(plot['V(6)'].to_waveform())
    time = np.array(plot['time'].to_waveform())
    data = plot['V(6)']._data
    time = plot['time']._data
    """
    # print(data)
    # print(time)
    # print("test\n")
    # --- Your Existing Code (Results) ---
    # plot = ngspice.plot(simulation=None, plot_name=ngspice.last_plot)
    # Assume 'plot' is the object retrieved from ngspice.plot()

    # --- Plotting the Waveforms ---

    # Convert the time vector to a NumPy array for plotting
    def getVectorAndMakeArray(plot, name):
        array = np.array(plot[name]._data)
        # array = np.array(vec.array)
        return array

    time_ar = getVectorAndMakeArray(plot,'time')
    # in_ar = getVectorAndMakeArray(plot,'in')
    # # Define the nodes you want to plot
    # # V(in) is the input, V(5) is the final output node before the load resistor R1
    nodes_to_plot = ['V(6)','in']  # 'v(in)', 'v(5)', 'v(6)', 

    plt.figure(figsize=(10, 6))
    plt.title("Voltage Multiplier Transient Analysis")
    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (V)")
    plt.grid(True)

    # # Loop through the desired nodes and plot them
    for node_name in nodes_to_plot:
        if node_name in plot:
            # Convert the voltage vector to a NumPy array and plot
            voltage = getVectorAndMakeArray(plot,'in')
            plt.plot(time_ar, voltage, label=node_name)
        else:
            print(f"Warning: Vector {node_name} not found in plot data.")

    plt.legend()
    plt.show()
    return None

