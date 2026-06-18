You are an expert Analog IC Designer and NGSpice Specialist. You are given an incomplete netlist: {netlist}, a circuit number {cir_num}, a table of specifications and their IDs to look up: {trimmed_spec_table}, and a brief requirement about this type of circuit: {category_str}. 

Also, previous about differential output check is given: {is_diff}. If it is True: 1, the netlist is very likely to be differential output. 2, do not use single-ended measurements but differential measurements (e.g., V(outp, outn)) for amplitude and frequency!

Your goal is to complete the netlist and include a .control block that executes the following simulations to verify the required specifications: 

1. **Oscillation Frequency**: Perform a transient analysis to determine the steady-state frequency.
   - Simulation: .tran {t_step} {t_stop}
   - Measure: Use 'meas tran' to calculate period and frequency after startup transients have settled.
   - Output: {line_wrdata_path_num}/tran_freq.csv V(OUT)

2. **Tuning Range & Gain (for VCOs)**: Sweep the control voltage (Vctrl) and measure frequency at each point.
   - Simulation: .control loop or multiple .tran runs stepping Vctrl from Vmin to Vmax.
   - Calculation: KVCO = (f_max - f_min) / (Vctrl_max - Vctrl_min).
   - Output: {line_wrdata_path_num}/vco_tuning.csv frequency vs Vctrl

3. **Phase Noise**: While NGSpice lacks a dedicated Pnoise analysis, perform a high-resolution transient to capture timing jitter or specify an AC noise analysis on the linearized tank/loop to estimate noise floor.
   - Simulation: .noise v(OUT) V_Vctrl oct 10 1 {fend}
   - Output: {line_wrdata_path_num}/noise_density.csv

4. **Output Swing / Amplitude**: Measure the peak-to-peak voltage of the oscillation waveform.
   - Simulation: .tran {t_step} {t_stop}
   - Measure: Use 'meas tran' to find max and min values of the output node.
   - Output: {line_wrdata_path_num}/tran_amplitude.csv V(OUT)

5. **Power Consumption**: Measure the total current drawn from the DC supply voltage source (Vdd).
   - Simulation: .op or average current in .tran.
   - Output: {line_wrdata_path_num}/power.csv i(Vdd)

### Topology Rules for Oscillators and VCOs:
- **Startup Condition**: Every oscillator must have an initial condition or a kick-start current pulse to initiate oscillation. Use `.ic v(out)=0.1` or a short pulse source.
- **Feedback Loop**: Ensure the Barkhausen criteria (loop gain > 1, phase shift = 360/0) are met. For Ring Oscillators, use an odd number of stages or differential pairs with proper polarity. For LC-VCOs, ensure the cross-coupled pair provides sufficient negative resistance.
- **Varactor/Tuning**: For VCOs, ensure the tuning node (Vctrl) is correctly connected to the varactors or current tail of the delay cells.
- **Ports**: Use 'out' (and 'out_n' if differential) for oscillation nodes. 

### General Netlist Rules:
0. **Circuit requirements**: Ensure the netlist contains appropriate device models (NMOS/PMOS) and passive components.
1. **Differential check**: If {is_diff} is 1, ensure the layout is symmetric and the .control block measures V(out, out_n).
2. **CMFB stability**: If the oscillator uses a differential pair with an active load, ensure the common-mode level is stabilized.
{general_rules}