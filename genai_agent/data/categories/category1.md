### 1. Single-Ended Baseband Voltage Amplifiers (Linear Gain Stages)
A fundamental gain block intended for signal conditioning, typically operating in the "small-signal" regime where linearity is assumed and crossover distortion is negligible. These circuits prioritize voltage gain accuracy, bandwidth, and feedback stability.

* **Ports:**
    * **Required:** **Exactly one** signal voltage input (High Impedance typical). *If a second signal input exists, it is Class 7 or 40.*
    * **Required:** Single voltage output (Medium/Low Impedance).
    * **Note:** Unlike RF amps, input impedance matching is rarely required; the focus is on voltage bridging ($Z_{in} \gg Z_{source}$).
* **Stimuli/Measurements:**
    * **Stimuli:** Small-signal AC voltage source; DC bias voltage.
    * **Measurements:**
        * **Voltage Gain ($A_v$) & Phase:** AC analysis to determine DC gain and the -3dB corner frequency.
        * **Stability (PM/GM):** **Critical.** Analysis of Phase Margin and Gain Margin to ensure the amplifier does not oscillate when placed in a feedback loop.
        * **PSRR:** AC analysis of supply rejection (often critical in baseband precision circuits). *(Note: CMRR is not applicable here as there is no accessible differential input pair).*
        * **Input-Referred Noise:** Voltage noise density ($nV/\sqrt{Hz}$) integration over the bandwidth.
        * **Slew Rate:** Transient analysis with a step response (strictly for settling time, not distortion).
* **Topologies:**
    * **Fundamental Stages:** Common-Source (CS), Common-Emitter (CE), Cascode, Telescopic Cascode, Folded Cascode.
    * **Multi-Stage:** Operational Amplifiers (Op-Amps) in open loop or fixed feedback configurations, OTA (Operational Transconductance Amplifiers).
    * **Internal Differential Structures:** 

 Includes circuits that use a **differential input pair internally** (e.g., an Op-Amp with feedback resistors or a self-biased reference on the inverting node) but **do not expose the second input** as a top-level port.
    * **Active Loads:** Current mirrors, active inductor loads (for bandwidth extension without RF tuning).
* **Rule:** The circuit is a **linear gain block** with a **Single-Input/Single-Output (SISO)** interface.
    * It is disqualified if it includes inductive source degeneration (indicates LNA).
    * It is disqualified if it relies on complementary switching devices for high-current output (indicates Push-Pull/Class AB).