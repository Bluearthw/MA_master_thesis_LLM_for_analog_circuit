nl_mar_15 = """* title line
.param IB1_val=0.01
.param w1=0.5u l1=90n m1=1
.param w0=0.5u l0=90n m0=1
.param w3=0.5u l3=90n m3=1
.param w2=0.5u l2=90n m2=1
.param r0_val=1k
.param trf=0.5u
.param period=10u
.param VDD_val=1.8
.param VCM_val=0.9
.param Cload_val=1p
.include "1genai/data/p045_TT.sp"
M1 VOUT1 net10 VDD VDD pmos w=w1 l=l1 m=m1
M0 net10 net10 VDD VDD pmos w=w0 l=l0 m=m0
M3 VOUT1 VIN2 tail VSS nmos w=w3 l=l3 m=m3
M2 net10 VIN1 tail VSS nmos w=w2 l=l2 m=m2
R1 net10 tail {r0_val}
I_bias tail 0 dc=IB1_val
vss VSS 0 dc=0
vdd VDD 0 dc=VDD_val
C1 VOUT1 VSS {Cload_val}
Vdm vid 0 dc=0 ac=1 PULSE(-0.72 0.72 1u 0.5u 0.5u 4.5u 10u)
Vcm_source VCM 0 dc=VCM_val
E1 VIN1 VCM vid 0 0.5
E2 VIN2 VCM vid 0 -0.5
.control
option numdgt=7
set temp=25
set units=degrees
set wr_vecnames
ac dec 10 1 100G
wrdata ./1genai/output/155/ac_gain.csv v(VOUT1)
dc Vcm_source 0 1.8 0.01
wrdata ./1genai/output/155/icmr.csv v(VOUT1)
dc Vdm -0.5 0.5 0.01
wrdata ./1genai/output/155/dc_vid.csv v(VOUT1)

noise v(VOUT1) Vdm dec 10 1 100G
wrdata ./1genai/output/155/noise_total.csv noise2.inoise_total

tran 10n 30u
wrdata ./1genai/output/155/tran_sr.csv v(VOUT1)
alter vdd ac=1
alter Vdm ac=0
ac dec 10 1 100G
wrdata ./1genai/output/155/psrr.csv v(VOUT1)
alter vdd ac=0
alter Vcm_source ac=1
ac dec 10 1 100G
wrdata ./1genai/output/155/cmrr.csv v(VOUT1)
.endc
.end"""

nl_mar_15_2 = """* title line

*params
.param IB1_val=0.01
.param w1=0.5u
.param l1=90n
.param m1=1
.param w0=0.5u
.param l0=90n
.param m0=1
.param w3=0.5u
.param l3=90n
.param m3=1
.param w2=0.5u
.param l2=90n
.param m2=1
.param r0=1k
.param trf=0.5u
.param period=10u
.param VDD_val=1.2
.param VCM_val=0.6
.param CL=1p

.include "1genai/data/p045_TT.sp"

* Circuit
M1 VOUT1 net10 VDD VDD pmos w=w1 l=l1 m=m1
M0 net10 net10 VDD VDD pmos w=w0 l=l0 m=m0
M3 VOUT1 VIN2 IB1 VSS nmos w=w3 l=l3 m=m3
M2 net10 VIN1 IB1 VSS nmos w=w2 l=l2 m=m2
R0 net10 IB1 {r0}
Cload VOUT1 VSS {CL}

* Sources
ib1 IB1 0 dc=IB1_val
vss VSS 0 dc=0
vdd VDD 0 dc=VDD_val

* Inputs for Differential/CM/Transient
Vdm vid 0 dc 0 ac 1 PULSE(-0.1 0.1 0.5u 0.5u 0.5u 5u 10u)
Vcm_src VCM 0 dc=VCM_val ac 0
E1 VIN1 VCM vid 0 0.5
E2 VIN2 VCM vid 0 -0.5

.control
option numdgt=7
set temp=25
set units=degrees
set wr_vecnames

* 1. AC Analysis for Gain, BW, PM, GM, Phase
alter vdm ac=1
alter vcm_src ac=0
alter vdd ac=0
ac dec 10 1 100G
wrdata ./1genai/output/155/ac_gain.csv v(VOUT1)

* 2. Noise Analysis
noise v(VOUT1) vdm dec 10 1 100G
wrdata ./1genai/output/155/noise.csv noise2.inoise_total

* 3. Transient Analysis for Slew Rate
tran 10n 20u
wrdata ./1genai/output/155/tran_sr.csv v(VOUT1)

* 4. Output Swing
dc vdm -0.6 0.6 0.01
wrdata ./1genai/output/155/out_swing.csv v(VOUT1)

* 5. ICMR
dc vcm_src 0 1.2 0.01
wrdata ./1genai/output/155/icmr.csv v(VOUT1)

* 6. PSRR
alter vdm ac=0
alter vcm_src ac=0
alter vdd ac=1
ac dec 10 1 100G
wrdata ./1genai/output/155/psrr.csv v(VOUT1)

* 7. CMRR
alter vdm ac=0
alter vcm_src ac=1
alter vdd ac=0
ac dec 10 1 100G
wrdata ./1genai/output/155/cmrr.csv v(VOUT1)

.endc
.end"""

nl_mar_17="""* title line
.param IB1=0.01
.param w1=0.5u l1=90n m1=1
.param w0=0.5u l0=90n m0=1
.param w3=0.5u l3=90n m3=1
.param w2=0.5u l2=90n m2=1
.param r0=1k
.param trf=0.5u
.param period=10u
.param VDD=1.2
.param Cload=1p
.param VCM=0.6
.include "1genai/data/p045_TT.sp"
M1 VOUT1 net10 VDD VDD pmos w=w1 l=l1 m=m1
M0 net10 net10 VDD VDD pmos w=w0 l=l0 m=m0
M3 VOUT1 VIN2 TAIL VSS nmos w=w3 l=l3 m=m3
M2 net10 VIN1 TAIL VSS nmos w=w2 l=l2 m=m2
R0 net10 TAIL {r0}
ib1 TAIL 0 dc=IB1
vss VSS 0 dc=0
v_vdd VDD 0 dc=VDD
cload VOUT1 VSS {Cload}
v_in_diff aid 0 dc=0 ac=1.0
v_vcm vicm 0 dc=0.6
e_p VIN1 vicm aid 0 0.5
e_n VIN2 vicm aid 0 -0.5
.control
option numdgt=7
set temp=25
set units=degrees
set wr_vecnames
ac dec 10 1 100G
wrdata ./1genai/output/155/ac_gain.csv v(VOUT1)
dc v_vcm 0 1.2 0.01
wrdata ./1genai/output/155/dc_icmr.csv v(VOUT1)
dc v_in_diff -0.6 0.6 0.01
wrdata ./1genai/output/155/dc_swing.csv v(VOUT1)
alter v_in_diff ac=0
alter v_vcm ac=1
ac dec 10 1 100G
wrdata ./1genai/output/155/ac_cmrr.csv v(VOUT1)
alter v_vcm ac=0
alter v_vdd ac=1
ac dec 10 1 100G
wrdata ./1genai/output/155/ac_psrr.csv v(VOUT1)


noise v(VOUT1) v_in_diff dec 10 1 100G
wrdata ./1genai/output/155/noise.csv inoise_spectrum

alter v_in_diff ac=0 dc=0
alter @v_in_diff[pulse] = [ -0.5 0.5 1n 0.5u 0.5u 4.5u 10u ]
tran 10n 20u
wrdata ./1genai/output/155/tran_sr.csv v(VOUT1)
.endc
.end"""


nl_96_diff_with_fake_cmfb_not_for_sim = """
* Circuit Components
M2 VOUT2 VIN2 net017 VSS nmos w=w2 l=l2 m=m2
M0 VOUT1 VIN1 net017 VSS nmos w=w0 l=l0 m=m0
M1 net017 VB1 VSS VSS nmos w=w1 l=l1 m=m1
M4 VOUT2 net017 VDD VDD pmos w=w4 l=l4 m=m4
M3 VOUT1 net017 VDD VDD pmos w=w3 l=l3 m=m3
"""

nl_182_diff_with_cmfb_not_for_sim ="""M5 (VOUT2 VB1 net36 VSS) nmos4
M4 (VOUT1 VB1 net32 VSS) nmos4
M1 (net32 VIN2 IB1 VSS) nmos4
M0 (net36 VIN1 IB1 VSS) nmos4
R1 (VOUT2 net29) resistor
R2 (net29 VOUT1) resistor
R0 (net36 net35) resistor
C1 (VDD net29) capacitor
C0 (net35 net32) capacitor
M3 (VOUT1 net29 VDD VDD) pmos4
M2 (VOUT2 net29 VDD VDD) pmos4"""

nl_182_diff_with_cmfb_before_cmfb_agent = """* Fully Differential Amplifier 182
.param VDD_val=1.1
.param VCM_val=0.55
.param Cload_val=1p
.param VB1=0.7
.param IB1=0.01
.param w5=0.5u
.param l5=90n
.param m5=1
.param w4=0.5u
.param l4=90n
.param m4=1
.param w1=0.5u
.param l1=90n
.param m1=1
.param w0=0.5u
.param l0=90n
.param m0=1
.param r1=1k
.param r2=1k
.param r0=1k
.param c1=3p
.param c0=3p
.param w3=0.5u
.param l3=90n
.param m3=1
.param w2=0.5u
.param l2=90n
.param m2=1
.param trf=0.5u
.param period=10u
.include "1genai/data/p045_TT.sp"

* Core Circuit
M5 VOUT2 VB1 net36 VSS nmos w=w5 l=l5 m=m5
M4 VOUT1 VB1 net32 VSS nmos w=w4 l=l4 m=m4
M1 net32 VIN2 IB1 VSS nmos w=w1 l=l1 m=m1
M0 net36 VIN1 IB1 VSS nmos w=w0 l=l0 m=m0
R1 VOUT2 net29 {r1}
R2 net29 VOUT1 {r2}
R0 net36 net35 {r0}
C1 VDD net29 {c1}
C0 net35 net32 {c0}
M3 VOUT1 net29 VDD VDD pmos w=w3 l=l3 m=m3
M2 VOUT2 net29 VDD VDD pmos w=w2 l=l2 m=m2

* Bias Sources
ib1 IB1 0 dc={IB1}
vb1 VB1 0 dc={VB1}
v_vdd VDD 0 dc {VDD_val}
vss VSS 0 dc 0
v_vcm VCM 0 dc {VCM_val}

* Loads
CL1 VOUT1 0 {Cload_val}
CL2 VOUT2 0 {Cload_val}

* Stimuli Sources
vid aid 0 dc 0 ac 1.0 PULSE(-0.1 0.1 1n 1n 1n 5u 10u)
vicm acm 0 dc 0 ac 0
ein1 VIN1 VCM aid 0 0.5
ein2 VIN2 VCM aid 0 -0.5

.control
option numdgt=7
set temp=25
set units=degrees
set wr_vecnames

* 1. Differential Gain and Phase Response
ac dec 10 1 100G
wrdata ./1genai/output/182/ac_gain.csv v(VOUT1) v(VOUT2)

* 2. Common-Mode Gain and CMRR setup
alter vid acmag=0
alter vicm acmag=1
ac dec 10 1 100G
wrdata ./1genai/output/182/ac_cm.csv v(VOUT1) v(VOUT2)

* 3. PSRR setup
alter vicm acmag=0
alter v_vdd acmag=1
ac dec 10 1 100G
wrdata ./1genai/output/182/ac_psrr.csv v(VOUT1) v(VOUT2)
alter v_vdd acmag=0

* 4. Noise analysis
alter vid acmag=1
noise v(VOUT1,VOUT2) vid dec 10 1 100G
setplot noise1
wrdata ./1genai/output/182/noise.csv inoise_spectrum

* 5. Slew Rate and Settling Time
tran 10n 20u
wrdata ./1genai/output/182/tran_sr.csv v(VOUT1) v(VOUT2)

.endc
.end"""

nl_182_before_cmfb_agent_cleaned = """* Fully Differential Amplifier 182
.param VDD_val=1.1
.param VCM_val=0.55
.param Cload_val=1p
.param VB1=0.7
.param IB1=0.01
.param w5=0.5u
.param l5=90n
.param m5=1
.param w4=0.5u
.param l4=90n
.param m4=1
.param w1=0.5u
.param l1=90n
.param m1=1
.param w0=0.5u
.param l0=90n
.param m0=1
.param r1=1k
.param r2=1k
.param r0=1k
.param c1=3p
.param c0=3p
.param w3=0.5u
.param l3=90n
.param m3=1
.param w2=0.5u
.param l2=90n
.param m2=1
.param trf=0.5u
.param period=10u
.include "1genai/data/p045_TT.sp"

* Core Circuit
M5 VOUT2 VB1 net36 VSS nmos w=w5 l=l5 m=m5
M4 VOUT1 VB1 net32 VSS nmos w=w4 l=l4 m=m4
M1 net32 VIN2 IB1 VSS nmos w=w1 l=l1 m=m1
M0 net36 VIN1 IB1 VSS nmos w=w0 l=l0 m=m0
R1 VOUT2 net29 {r1}
R2 net29 VOUT1 {r2}
R0 net36 net35 {r0}
C1 VDD net29 {c1}
C0 net35 net32 {c0}
M3 VOUT1 net29 VDD VDD pmos w=w3 l=l3 m=m3
M2 VOUT2 net29 VDD VDD pmos w=w2 l=l2 m=m2

* Bias Sources
ib1 IB1 0 dc={IB1}
vb1 VB1 0 dc={VB1}
v_vdd VDD 0 dc {VDD_val}
vss VSS 0 dc 0
v_vcm VCM 0 dc {VCM_val}

* Loads
CL1 VOUT1 0 {Cload_val}
CL2 VOUT2 0 {Cload_val}

* Stimuli Sources
vid aid 0 dc 0 ac 1.0 PULSE(-0.1 0.1 1n 1n 1n 5u 10u)
vicm acm 0 dc 0 ac 0
ein1 VIN1 VCM aid 0 0.5
ein2 VIN2 VCM aid 0 -0.5

.control
option numdgt=7
set temp=25
set units=degrees
set wr_vecnames
.endc
.end"""

nl_182_after_cmfb_agent = """* Fully Differential Amplifier 182 - CMFB Stability Analysis
.param VDD_val=1.1
.param VCM_val=0.55
.param VCMFB_REF=0.55
.param Cload_val=1p
.param VB1=0.7
.param IB1=0.01
.param w5=0.5u
.param l5=90n
.param m5=1
.param w4=0.5u
.param l4=90n
.param m4=1
.param w1=0.5u
.param l1=90n
.param m1=1
.param w0=0.5u
.param l0=90n
.param m0=1
.param r1=1k
.param r2=1k
.param r0=1k
.param c1=3p
.param c0=3p
.param w3=0.5u
.param l3=90n
.param m3=1
.param w2=0.5u
.param l2=90n
.param m2=1
.param trf=0.5u
.param period=10u
.include "genai_agent/data/p045_TT.sp"

* Core Circuit
* M5 and M4 are NMOS Cascodes
M5 VOUT2 VB1 net36 VSS nmos w=w5 l=l5 m=m5
M4 VOUT1 VB1 net32 VSS nmos w=w4 l=l4 m=m4
* M1 and M0 are the Differential Input Pair
M1 net32 VIN2 IB1 VSS nmos w=w1 l=l1 m=m1
M0 net36 VIN1 IB1 VSS nmos w=w0 l=l0 m=m0
* CMFB Sensing Resistors - net29 is the sensed CM voltage
R1 VOUT2 net29 {r1}
R2 net29 VOUT1 {r2}
* Compensation/Degeneration
R0 net36 net35 {r0}
C0 net35 net32 {c0}
* PMOS Loads and CMFB Control Gates (gate_fb)
* C1 is attached to the high-impedance control node for compensation
C1 VDD gate_fb {c1}
M3 VOUT1 gate_fb VDD VDD pmos w=w3 l=l3 m=m3
M2 VOUT2 gate_fb VDD VDD pmos w=w2 l=l2 m=m2

* CMFB Loop Break for AC Analysis
* This source shorts net29 and gate_fb for DC, and injects 1V AC between them
v_cmfb_break net29 gate_fb dc 0 ac 1

* Bias Sources
ib1 IB1 0 dc={IB1}
vb1 VB1 0 dc={VB1}
v_vdd VDD 0 dc {VDD_val}
vss VSS 0 dc 0
v_vcm VCM 0 dc {VCM_val}

* Loads
CL1 VOUT1 0 {Cload_val}
CL2 VOUT2 0 {Cload_val}

* Stimuli Sources
* Differential AC is set to 0 for CMFB stability measurement
vid aid 0 dc 0 ac 0
vicm acm 0 dc 0 ac 0
ein1 VIN1 VCM aid 0 0.5
ein2 VIN2 VCM aid 0 -0.5

.control
option numdgt=7
set temp=25
set units=degrees
set wr_vecnames

* AC Sweep for CMFB Loop Gain (T = v(net29)/v(gate_fb))
ac dec 50 1 100G

* Write loop gain data to CSV
* The following agent will analyze v(net29)/v(gate_fb) to determine Phase Margin and GBW
wrdata ./1genai/output/182/cmfb_stb.csv v(net29)/v(gate_fb)

.endc
.end
"""

nl_timeout = """
* title line
.param VB1=0.6
.param VDD=1
.param vcm=0.6
.param w0=1.2757836193589348e-06
.param l0=2.065025743856232e-07
.param m0=9
.param w1=1.4819912678863445e-06
.param l1=1.1281494891414084e-07
.param m1=11
.param trf=1.3187112284561464e-12
.param period=8.418525324287674e-12
.param Cload=1.3570013470771993e-12
.include "genai_agent/data/p045_TT.sp"
M0 VOUT1 VB1 VDD VDD pmos w=w0 l=l0 m=m0
M1 VOUT1 VIN1 VSS VSS nmos w=w1 l=l1 m=m1
CLOAD VOUT1 VSS {Cload}
vdd VDD 0 dc=VDD
vb1 VB1 0 dc=VB1
vss VSS 0 dc=0
vin VIN1 0 dc=vcm ac=1.0 PULSE(0.5 0.7 {trf} {trf} {trf} {0.5*period-trf} {period})
.control
option numdgt=7
set temp=25
set units=degrees
set wr_vecnames
ac dec 10 1 100G
wrdata ./genai_agent/output/9/ac_gain.csv v(VOUT1)
noise v(VOUT1) vin dec 10 1 100G

wrdata ./genai_agent/output/9/noise.csv inoise_total
tran 1u 20u
wrdata ./genai_agent/output/9/tran_SR.csv v(VOUT1)
.endc
.end
"""

"""



alter vdd ac=1.0
alter vin ac=0
ac dec 10 1 100G
wrdata ./genai_agent/output/9/psrr.csv v(VOUT1)"""

nl_april_sim_failed_warning = """* title line
.param VB1=0.7
.param VDD=1.2
.param VCM=0.6
.param wp0=2.0582877e-06
.param lp0=1.0085766e-07
.param mp0=23
.param wn1=8.9782213e-07
.param ln1=1.7089069e-07
.param mn1=11
.param trf=0.5u
.param period=10u
.param Cload=7.985418e-13
.include "genai_agent/data/p045_TT.sp"
mp0 VOUT1 VB1 VDD VDD pmos w=wp0 l=lp0 m=mp0
mn1 VOUT1 VIN1 VSS VSS nmos w=wn1 l=ln1 m=mn1
Cload VOUT1 VSS {Cload}
vdd VDD 0 dc=VDD ac=0
vss VSS 0 dc=0
vb1 VB1 0 dc=VB1
vin VIN1 VSS dc=VCM ac=1.0 PULSE(0 1.2 0.5u 0.5u 0.5u 4.5u 10u)
.control
option numdgt=7
set temp=25
set units=degrees
set wr_vecnames
ac dec 10 1 100G
wrdata ./genai_agent/output/9/ac_gain.csv v(VOUT1)
noise v(VOUT1) vin dec 10 1 100G
setplot noise1
wrdata ./genai_agent/output/9/noise.csv inoise_spectrum
alter vdd ac=1
alter vin ac=0
ac dec 10 1 100G
wrdata ./genai_agent/output/9/psrr.csv v(VOUT1)
dc vdd 1.2 1.2 1
wrdata ./genai_agent/output/9/dc_current.csv i(vdd)
tran 50n 30u
wrdata ./genai_agent/output/9/tran_SR.csv v(VOUT1)
.endc
.end"""

nl_155_failed = """* title line

*params
.param IB1=0.01
.param wp1=2.5060679985787825e-06 lp1=1.0551991398020154e-07 mp1=14
.param wp0=2.6146664430949156e-06 lp0=1.1281494891414084e-07 mp0=3
.param wn3=6.059618692231604e-07 ln3=2.065025743856232e-07 mn3=21
.param wn2=1.4819912678863445e-06 ln2=9.1885681055841e-08 mn2=11
.param r0=1k
.param trf=0.5u
.param period=10u
.param VDD=1.2
.param VCM=0.6
.param Cload=1.3570013470771993e-12

.include "genai_agent/data/p045_TT.sp"

* Circuit Components
mp1 VOUT1 net10 VDD VDD pmos w=wp1 l=lp1 m=mp1
mp0 net10 net10 VDD VDD pmos w=wp0 l=lp0 m=mp0
mn3 VOUT1 VIN2 IB1 VSS nmos w=wn3 l=ln3 m=mn3
mn2 net10 VIN1 IB1 VSS nmos w=wn2 l=ln2 m=mn2
R0 net10 IB1 {r0}

ib1 IB1 0 dc=IB1
vdd VDD 0 dc=VDD
vss VSS 0 dc=0
Cload VOUT1 VSS {Cload}

* Signal Sources
Vdiff aid 0 dc=0 ac=1.0 PULSE({-VDD*0.5} {VDD*0.5} 0.1u 0.1u 0.1u {0.5*period} {period})
VVCM VCM 0 dc=VCM
ein1 VIN1 VCM aid 0 0.5
ein2 VIN2 VCM aid 0 -0.5

.control
option numdgt=7
set temp=25
set units=degrees
set wr_vecnames

* 1. DC Gain, Bandwidth, Phase Margin
alter vdiff ac=1.0
alter VVCM ac=0.0
alter vdd ac=0.0
ac dec 10 1 1T
wrdata ./genai_agent/output/155/ac_gain.csv v(VOUT1)

* 2. CMRR (Common Mode Gain)
alter vdiff ac=0.0
alter VVCM ac=1.0
alter vdd ac=0.0
ac dec 10 1 1T
wrdata ./genai_agent/output/155/ac_cmrr.csv v(VOUT1)

* 3. PSRR
alter vdiff ac=0.0
alter VVCM ac=0.0
alter vdd ac=1.0
ac dec 10 1 1T
wrdata ./genai_agent/output/155/ac_psrr.csv v(VOUT1)

* 4. Slew Rate / Transient
alter vdiff dc=0
tran 10n 20u
wrdata ./genai_agent/output/155/tran_SR.csv v(VOUT1)

* 5. Noise
noise v(VOUT1) Vdiff dec 10 1 1T
wrdata ./genai_agent/output/155/noise.csv inoise_total

.endc
.end"""