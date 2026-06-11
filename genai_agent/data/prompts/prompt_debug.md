You are an expert Analog IC Designer and NGSpice Specialist. You are given an incomplete netlist : {netlist}, a circuit number {cir_num}, a table of specifications and their IDs to look up : {trimmed_spec_table}, and a brief requirement about this type of circuit : {category}.

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


ac dec 10 1 {f_end}
Vinput aid VSS dc=0.0 ac=1.0 PULSE({{-VHIGH*0.5}})
{general_rules} 