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
# .include "D:\\1kulStudy\\8MA_Thesis\\material\\PDK\\45nm.sp"
circuit = '''
.include "1genai/data/45nm.sp"

* Global parameters
.param VDD_VAL=1.2V
.param VSS_VAL=0V
.param R0_VAL=1k
.param C0_VAL=10p
.param AC_MAG=1V

* DC Sources
VDD VDD 0 DC VDD_VAL
VSS VSS 0 DC VSS_VAL

* AC Source for AC simulation (applied to VDD for PSRR, or to a separate input if needed)
* For output impedance, we would apply an AC current source at VOUT1 and measure voltage.
* For PSRR, we apply AC to VDD.
VAC_VDD VDD 0 AC AC_MAG

* Transistor M0 (VDD VDD VOUT1 VSS) nmos4
* The example uses 'nmos' and 'pmos' models, so we'll use 'nmos' here.
* Assuming default W/L if not specified, or add W= L= if needed.
M0 VDD VDD VOUT1 VSS nmos W=1u L=45n

* Resistor R0 (VOUT1 VSS) resistor
* The example uses 'rc' for resistor and 'cc' for capacitor, but the problem states 'resistor' and 'capacitor'
* and no model is needed. So we use R and C directly.
R0 VOUT1 VSS R0_VAL

* Capacitor C0 (VOUT1 VSS) capacitor
C0 VOUT1 VSS C0_VAL

.control
* DC Operating Point Analysis
op

* AC Analysis for Output Impedance (Zout) and PSRR
* To measure Zout, we would typically inject an AC current at VOUT1 and measure VOUT1.
* To measure PSRR, we apply an AC voltage to VDD (as VAC_VDD above) and measure VOUT1.
* Let's perform AC analysis to see the response of VOUT1 to VAC_VDD (PSRR).
ac dec 10 1 1G
plot vdb(vout1) vp(vout1)

* Save AC results
wrdata ./ac_results.txt v(vout1)

.endc

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

