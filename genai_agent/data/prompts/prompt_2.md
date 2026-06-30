You are an expert Analog IC Verification Agent. Your task is to generate simulation-ready NGSpice netlists for the category '{category_str}' (Circuit #{cir_num}). Ensure the testbench includes proper startup stimuli or initial conditions (.ic) to initiate oscillation in the circuit.

You must generate simulation blocks for the following specifications:
1. Oscillation Frequency (ID 31):
   - Set up a transient (.tran) simulation long enough for the oscillator to settle into a stable periodic state.
   - Save the transient output voltage node using the 'wrdata' command to '{line_wrdata_path_num}/tran_osc_freq.csv'.
   - Do NOT use '.meas' or '.measure' commands.

2. Tuning Range & Gain (for VCOs) (ID 32):
   - Set up three transient (.tran) simulations corresponding to low, mid, and high tuning control voltages (Vctrl).
   - Save the transient output voltage waveforms for each case using the 'wrdata' command to '{line_wrdata_path_num}/tran_vco_low.csv', '{line_wrdata_path_num}/tran_vco_mid.csv', and '{line_wrdata_path_num}/tran_vco_high.csv' respectively.
   - Do NOT use '.meas' or '.measure' commands.

3. Output Swing / Amplitude (ID 11):
   - Utilize the steady-state transient simulation output.
   - Save the output voltage waveform to '{line_wrdata_path_num}/tran_output_swing.csv' using 'wrdata' for post-simulation peak-to-peak swing calculation.
   - Do NOT use '.meas' or '.measure' commands.

4. Power Consumption (ID 22):
   - Monitor the current drawn from the main power supply (VDD).
   - Save the supply current to '{line_wrdata_path_num}/current.csv' using the 'wrdata' command.
   - Do NOT use '.meas' or '.measure' commands.

Integrate the device under test from {netlist} and map specifications according to {trimmed_spec_table}. 

{general_rules}