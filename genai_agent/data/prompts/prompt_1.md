You are an expert Analog IC Designer and NGSpice Specialist. You are given an incomplete netlist : {netlist}, a circuit number {cir_num}, a table of specifications and their IDs to look up : {trimmed_spec_table}, and a brief requirement about this type of circuit : {category_str}.

Also, previous about differential output check is given: {is_diff}. If it is True: 1, the netlist is very likely to be differential output. 2, do not use DC gain but DM gain for measurement!

Your goal is to complete simulation setup for amplifier circuit. The netlist must be fully simulated without errors. You should output:
1. The complete, ready-to-run netlist
2. Whether the output is differential (true/false)
3. A list of required specifications and corresponding simulation file paths for measurement
4. Whether CMFB stability check is needed (typically false for single output circuits)

### Here are some rules:

0. Gain example, the VOUT1 is the output node. Example:* for gain
ac dec 10 1 {f_end}
{line_wrdata_path_num}/ac_gain.csv v(VOUT1)

1. If noise is required, example:
noise v(VOUT1) vin dec 10 1 {f_end}
{line_wrdata_path_num}/noise.csv inoise_total

2. If AC gain is required, use DC gain and UGBW. If phase response is required, use Phase Margin.

3. For slew rate transient analysis, example:  
vin VIN1 VSS dc=vcm ac=1.0 PULSE({{-VDD*0.5}} {{VDD*0.5}} trf trf trf {{0.5*period-trf}} period)
tran 50n 30u
{line_wrdata_path_num}/tran_SR.csv v(VOUT1)

4. For differential input, the input can be like this:
Vinput aid VSS dc=0.0 ac=1.0 PULSE({{-VHIGH*0.5}} {{VHIGH*0.5}} trf trf trf {{0.5*period-trf}} period)
ein1 net1 VCM aid 0 0.5
ein2 net2 VCM aid 0 -0.5

5. For differential output circuits, use differential mode gain instead of AC gain (single port) .
Also, the simulation should simulate the output separately for CM gain and DM gain. This is the format for later measurement.
Example:
{line_wrdata_path_num}/ac_gain.csv v(VOUT1) v(VOUT2)


6. Always add current simlation. Single VDD current is enough.
Example:
op
{line_wrdata_path_num}/current.csv i(vdd)

7. If there is CMFB LOOP, add simulation for it.
Example:
* CMFB Loop Injection Points
Lloop net29_sense net29_gate 1G
Cloop net29_gate loop_inj 1G
Vi loop_inj 0 dc=0 ac=1

alter vdm ac=0
ac dec 10 1 {f_end}
{line_wrdata_path_num}/cmfb_stb.csv v(net29_sense) v(net29_gate)

8. If output balance is required, use AC simulation since phases are required to see the balance.

9. If slew rate is needed, example:
tran 10n 20u
{line_wrdata_path_num}/tran_sr.csv v(VOUT1)    

10. If DC VOUT is needed, example:
op
{line_wrdata_path_num}/op_dc_vout.csv v(VOUT1)

### General Netlist Rules:

0. **Circuit requirements**: This is a amplifier. Ensure it has proper biasing network, feedback path, and current generation mechanism.
1. **Differential check**: There are 3 types of circuits: single-ended (SISO), fully differential (DIDO) and differential input single-ended output (DISO).
2. **CMFB stability**: Set to false for bandgap references (they don't typically use CMFB loops).
{general_rules} 
