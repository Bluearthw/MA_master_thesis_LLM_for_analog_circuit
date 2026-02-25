* title line
.param VDD=1.2
.param w1=0.5u l1=90n m1=1
.param w0=0.5u l0=90n m0=1
.param r0=1k
.param cload=1p
.param vbias=0.6
.include "1genai/data/p045_TT.sp"
M1 VOUT1 VIN1 net2 VSS nmos w=w1 l=l1 m=m1
M0 VSS VSS net2 VDD pmos w=w0 l=l0 m=m0
R0 VDD VOUT1 {r0}
CL VOUT1 VSS {cload}
vdd VDD 0 dc={VDD}
vss VSS 0 dc=0
vin1 VIN1 0 dc={vbias} ac=1 pulse(0.5 0.7 10n 1n 1n 100n 200n)
.control
option numdgt=4
set temp=25
set units=degrees
set wr_vecnames
ac dec 10 1 10G
wrdata ./1genai/output/ac_gain.csv v(VOUT1)
noise v(VOUT1) vin1 dec 10 1 10G
wrdata ./1genai/output/noise.csv onoise_spectrum inoise_spectrum
alter @vin1[acmag]=0
alter @vdd[acmag]=1
ac dec 10 1 10G
wrdata ./1genai/output/psrr.csv v(VOUT1)
alter @vdd[acmag]=0
tran 1n 500n
wrdata ./1genai/output/tran_slew.csv v(VOUT1) v(VIN1)
.endc
.end