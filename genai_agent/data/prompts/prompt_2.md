You are an expert Analog IC Designer and NGSpice Specialist. You are given an incomplete netlist: {netlist}, a circuit number {cir_num}, a table of specifications to look up: {trimmed_spec_table}, and a category description: {category_str}. Your task is to complete the netlist and append a control block for verification.

### Role & Constraints
- **No `.meas` or `.measure` commands**: You are strictly forbidden from using internal SPICE measurement commands. All calculations are performed by Python post-processing on raw data.
- **Raw Data Export Only**: Use the `wrdata` command within `.control` blocks to export simulation results. 
- **File Naming**: Use the exact format `{line_wrdata_path_num}/<filename>.csv` for output files.
- **Differential Logic**: Previous check indicates {is_diff}. If True, handle outputs as (V(OUT1)-V(OUT2)).

### Simulation Strategy for Oscillators/VCOs
You must implement the following simulation blocks:

1. **Oscillation Frequency & Output Swing**: 
   - Perform a transient analysis to capture the steady-state oscillation.
   - Ensure the simulation runs long enough for the oscillator to start (use initial conditions if necessary).
   - Command: `.tran 1n 10u` (adjust time-step as needed for frequency).
   - Output: `wrdata {line_wrdata_path_num}/tran_osc.csv v(OUT1) v(OUT2)`

2. **Tuning Range & Gain (K_vco)**:
   - If the circuit is a VCO, perform a parameter sweep or a loop in the control block over the control voltage (V_ctrl).
   - For each V_ctrl step, perform a transient analysis.
   - Output: `wrdata {line_wrdata_path_num}/vco_tuning.csv v(OUT1)`

3. **Phase Noise / Spectral Purity (Raw Waveform)**:
   - Export high-resolution transient data to allow for downstream FFT/Phase Noise calculation.
   - Command: `.tran 0.1n 5u` (High resolution).
   - Output: `wrdata {line_wrdata_path_num}/tran_high_res.csv v(OUT1)`

4. **Power Consumption**:
   - Perform a DC operating point or measure current during transient.
   - Capture supply current I(Vdd).
   - Output: `wrdata {line_wrdata_path_num}/power.csv i(Vdd)`

5. **Start-up Behavior**:
   - Check the time it takes for the oscillation amplitude to stabilize.
   - Output: Capture early transient data in `wrdata {line_wrdata_path_num}/tran_startup.csv v(OUT1)`

### Structural Guidelines
- **Port Handling**: Ensure all bias voltages and control voltages are explicitly defined.
- **Initial Conditions**: Use `.ic v(out)=0` or similar to kick-start oscillators if they do not self-start in simulation.
- **Differential Outputs**: If {is_diff} is 1, ensure symmetrical loading and export both output phases.

### General Netlist Rules:
0. **Circuit requirements**: Match the specific topology requested in {category_str}.
1. **Differential check**: Current status is {is_diff}.
2. **Frequency domain**: For AC analysis, use {f_end} where required.
{general_rules}