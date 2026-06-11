### 39. Output Drivers & Power Amplifiers (Push-Pull / Class B / AB)
High-current driver stages designed to drive low-impedance loads (speakers, transmission lines, antennas) or capacitive loads. These circuits operate in the "large-signal" regime where **efficiency** and **crossover distortion** are the dominant concerns.

* **Ports:**
    * **Required:** Input (may be single-ended or split complementary inputs for High-Side/Low-Side driving).
    * **Required:** Output (High current capability / Low $Z_{out}$).
* **Stimuli/Measurements:**
    * **Stimuli:** Large-signal Sine Wave (close to rail-to-rail) or Pulse train.
    * **Measurements:**
        * **Total Harmonic Distortion (THD):** **Critical.** Transient analysis + Fourier Transform (FFT) to detect crossover distortion and clipping. Small-signal AC analysis hides these faults.
        * **Efficiency (PAE / Drain Eff):** Measurement of Power Out vs. DC Power Consumed.
        * **Load-Pull:** (For RF PAs) Varying load impedance to find optimal power/efficiency contours.
        * **Quiescent Current:** DC sweep to tune the "dead zone" in Class AB stages.
* **Topologies:**
    * **Push-Pull Output Stages:** Class B, Class AB (using diode-connected biasing or $V_{be}$ multipliers).
    * **Complementary Drivers:** CMOS Inverter-based amplifiers (used as analog drivers), Quasi-Complementary (NPN+NPN) stages.
    * **Source/Emitter Followers:** Specifically large-device buffers intended for current gain (Current Buffers).
* **Rule:** The circuit utilizes **complementary devices** (N-type and P-type) or split paths to fundamentally handle **sourcing and sinking current** separately.
    * Identified by a "totem-pole" output structure.
    * Distinguished from Class 1 by the requirement for THD/FFT analysis rather than just Phase Margin.