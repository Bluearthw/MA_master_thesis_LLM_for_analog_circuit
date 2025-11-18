import PySpice.Logging.Logging as Logging
logger = Logging.setup_logging()


from PySpice.Spice.NgSpice.Shared import NgSpiceShared
import matplotlib.pyplot as plt
import numpy as np

ngspice = NgSpiceShared.new_instance()

# print(ngspice.exec_command('version -f'))
# print(ngspice.exec_command('print all'))
# print(ngspice.exec_command('devhelp'))
# print(ngspice.exec_command('devhelp resistor'))

circuit = '''
.include "./1genai/data/45nm.sp"

* Parameters
.param VDD=1.2
.param VSS=0

* DC Source
Vdd VDD 0 dc={VDD}

* AC Source for AC Analysis
Vac VOUT1 0 ac=1

* Components
M0 VDD VDD VOUT1 VSS nmos w=500n l=45n
rc VOUT1 VSS 1k
cc VOUT1 VSS 1p

.control
op      * Run Operating Point first
tran 0.1s 10s   * Then run Transient
ac dec 10 1k 100k * Finally run AC analysis
.endc
.end


'''

ngspice.load_circuit(circuit)

# print('Loaded circuit:')
# print(ngspice.listing())

# print(ngspice.show('c3'))
# print(ngspice.showmod('c3'))

ngspice.run()

print('Plots:\n', ngspice.plot_names)
# print('ressource_usage:\n ',ngspice.ressource_usage())
# print('status\n', ngspice.status())

plot = ngspice.plot(simulation=None, plot_name=ngspice.last_plot)

# ngspice.quit()

# print("\ntest")
print('plot?\n',plot)
# print(plot['in'])
""" this works
data = np.array(plot['V(6)'].to_waveform())
time = np.array(plot['time'].to_waveform())
data = plot['V(6)']._data
time = plot['time']._data
"""
# data = plot['V(6)']._data
# time = plot['time']._data
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

