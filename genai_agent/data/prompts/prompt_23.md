You are an expert Analog IC Designer and NGSpice Specialist. You are given a netlist for a charge pump circuit: {netlist}, circuit number {cir_num}, a table of specifications and their IDs: {trimmed_spec_table}, and detailed requirements: {category}.
Your goal is to complete the simulation setup for the charge pump circuit. The netlist must be fully simulated without errors. You should output:
1. The complete, ready-to-run netlist
2. Whether the output is differential (true/false)
3. A list of required specifications and corresponding simulation file paths for measurement
4. Whether CMFB stability check is needed (typically false for charge pump circuits)

### Charge Pump-Specific Rules and Measurements:
**Simulation Examples**:
1. **Current Matching**: Perform two separate DC sweeps of the output node to characterize the source and sink currents across the full compliance range.   
    - Simulation:   Phase A (Source): Force the UP logic input to VDD and the DN input to 0. Sweep a DC voltage source at the output (VCONT1) from 0 to VDD.   
                    Phase B (Sink): Force the DN logic input to VDD and the UP logic input to 0. Sweep the same DC voltage source at the output from 0 to VDD.   
    - Example:
    - Subcircuit can be removed or use ideal block if it is not needed. 
    * Declare helping netlist. The numbers can change if needed. 1.2 is VDD. 
    vgate_n net3 0 pulse(0   1.2 10ns 50ps 50ps 400ps 20ns) 
    vgate_p net4 0 pulse(1.2 0   10ns 50ps 50ps 400ps 20ns)

    vout_force VCONT1 0 dc=0.6
    .ic v(VCONT1) = 0.6
    .control
    ...
    * 1a. Measure Source Current (PMOS ON, NMOS OFF)
    alter vgate_p dc=0
    alter vgate_n dc=0
    dc vout_force 0 1.2 0.01
    - Output: {line_wrdata_path_num}/ source_current.csv i(vout_force)
    
    * 1b. Measure Sink Current (PMOS OFF, NMOS ON)
    alter vgate_p dc=1.2
    alter vgate_n dc=1.2
    dc vout_force 0 1.2 0.01
    - Output: {line_wrdata_path_num}/ sink_current.csv i(vout_force)

2. **Output Ripple**: Apply simultaneous, narrow, identical pulses to both `UP` and `DN` inputs to simulate a locked PFD state, and measure the peak-to-peak voltage variation on the output node with the load capacitor.
    - Simulation: narrow simultaneous pulses on UP and DN, transient analysis.
    - Output: {line_wrdata_path_num}/output_ripple.csv v(VOUT1)

3. **Voltage Compliance Range**: Sweep the DC voltage at the charge pump output node and measure the output current to determine the operating voltage range where sourced and sinked currents remain matched.
    - Simulation: Same as current matching, no more simulation needed.
    - Output: Same as current matching, use those 2 paths. So, there are 2 spec_sim terms.

4. **Average supply current**: Need to know the current for power. Since it is with clock, transient analysis is required.
    - Simulation: careful about the clock definition and the trans signal
    - Output: {line_wrdata_path_num}/current.csv vdd#branch

5. **subcircuit**: They can be removed and use ideal blocks. If needed, there are examples:
    
    .subckt INVERTER in out vdd vss
    B1 out vss v = (v(in) > (v(vdd)/2)) ? v(vss) : v(vdd)
    .ends INVERTER
    
    .subckt PFD clka clkb up dn vdd vss
    B1 up vss V=V(clka)
    B2 dn vss V=V(clkb)
    .ends
7. If DC Vout is required: Initial operating point to determine nominal VOUT_REF
   - Simulation: op
   - Output: {line_wrdata_path_num}/op_vout_ref.csv v(VOUT1)

### General Netlist Rules:

0. **Circuit requirements**: This is a charge pump circuit. Ensure it has proper switching network, capacitors, and control logic for voltage multiplication.
1. **Differential check**: Charge pump outputs are typically single-ended (non-differential), so output differential=false unless proven otherwise.
2. **CMFB stability**: Set to false for charge pump circuits (they don't typically use CMFB loops).
{general_rules} 