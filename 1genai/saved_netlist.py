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