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

* Global parameters
.param VDD_VAL=1.2
.param VSS_VAL=0
.param R0_VAL=10k
.param C0_VAL=10p
.param AC_MAG=1

* DC sources
VDD VDD 0 dc={VDD_VAL}
VSS VSS 0 dc={VSS_VAL}

* AC source for AC simulation
VAC_VDD VDD_AC VSS_AC ac={AC_MAG}

* Circuit definition
* M0 (Drain Gate Source Bulk) nmos4
M0 VDD VDD VOUT1 VSS nmos4 w=1u l=90n

* R0 (net1 net2) resistor
R0 VOUT1 VSS resistor r={R0_VAL}

* C0 (net1 net2) capacitor
C0 VOUT1 VSS capacitor c={C0_VAL}

.control
* DC operating point analysis
op

* AC analysis to find output impedance (Zout)
* We apply an AC source to VDD and measure VOUT1.
* The output impedance is effectively the transfer function from VDD_AC to VOUT1,
* but since the input is tied to VDD, we are looking at the supply rejection.
* To measure Zout, we would typically inject a current at VOUT1 and measure voltage,
* or apply a voltage at VOUT1 and measure current.
* For this specific circuit, given the input is tied to VDD,
* we will simulate the transfer function from VDD to VOUT1 for AC analysis.
* If Zout is strictly required, an additional AC current source at VOUT1 would be needed.
* For now, we will simulate the AC response of VOUT1 to VDD variations.
ac dec 10 1 1G
print v(VOUT1)
*wrdata ac_vout1.txt v(VOUT1)

quit
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
# print('plot?\n',plot)
# print(plot['in'])
""" this works
data = np.array(plot['V(6)'].to_waveform())
time = np.array(plot['time'].to_waveform())
data = plot['V(6)']._data
time = plot['time']._data
"""
data = plot['V(6)']._data
time = plot['time']._data
print(data)
print(time)
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

