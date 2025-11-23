GOOGLE_API_KEY="AIzaSyBCCHDhKIabEjdhfFI0vyXBM6Fc_AhhKQY"

# netlist 9
netlist_with_load ="""*params

.param VDD=1.2
.param r0=1k
.param c0=3p
.include "1genai/data/45nm.sp"

"M0 VDD VDD VOUT1 VSS nmos
R0 VOUT1 VSS {r0}
C0 VOUT1 VSS {c0}
* dgsb

Vdd VDD 0 dc=VDD

Vss VSS 0 dc=0
"""

# netlist 6
netlist_without_load ="""*params

.param VDD=1.2
.param w1=0.5u l1=90n m1=1
.include "1genai/data/45nm.sp

"M0 VOUT1 VB1 VDD VDD pmos
M1 VOUT1 VIN1 VSS VSS nmos w=w1 l=l1 m=m1

Vdd VDD 0 dc=VDD

Vss VSS 0 dc=0"""