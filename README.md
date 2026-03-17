git add .
git commit -m "finish output swing, category 7"
git push

venv\Scripts\Activate.ps1
# MA_master_thesis_LLM_for_analog_circuit

number of netlists : 894
"amplifier" and "Amplifier"
opamp : 470
SISO_opamps : 334
SISO_opamps without clk Iin Iout : 289
SISO_opamps with only VB,VIN1,VOUT1 and VBn : 171


69, 77 is differential
# RF
    LNA, PA, DA / IGA??
    not RF: 9, 166
467 has L and it is LNA (low nosie) for RF
465 does not have L but it is also RF
456, with IB 
522 works like a bandpass
578 with L, it is PA (power)
643 is a schimtt trigger including amplifier
832 is 3 stages
906 2 stage with feedback
1017 parallel path
# comparator, actually, if there is vin2, it is CMP
with "amplifier" :
    1039
    1041, at line 8
