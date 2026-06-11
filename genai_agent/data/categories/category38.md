### 38. Single-Ended RF Low-Noise Amplifiers (SISO LNA)
A fundamental RF gain block with a strict **Single-Input / Single-Output (SISO)** interface. Designed for $50\Omega$ impedance matching, low noise, and power gain.
* **Ports**:
    * **Required**: Exactly **ONE** RF Input Port (Single-ended, e.g., `RFin`/`IN`).
    * **Required**: Exactly **ONE** RF Output Port (Single-ended, e.g., `RFout`/`OUT`).
    * **Exclusion**: If the circuit has `inp`/`inn` or `outp`/`outn`, it is **disqualified** (Move to Class 20).
* **Stimuli/Measurements**:
    * **Stimuli**: S-Parameter Ports ($Z_0 = 50\Omega$) and Harmonic Balance sources.
    * **Measurements**:
        * **S-Parameters ($S_{11}, S_{22}, S_{21}$)**: **Critical.** Verification of Input Return Loss ($S_{11} < -10\text{dB}$), Output Return Loss, and Transducer Gain.
        * **Noise Figure (NF)**: **Critical.** Measured in dB, accounting for source thermal noise.
        * **Stability ($K$-Factor/$\mu$-Factor)**: Stern stability analysis to ensure unconditional stability ($K>1$).
        * **Linearity ($IIP3 / P_{1dB}$)**: Two-tone test.
* **Topologies**:
    * **Inductively Degenerated Common-Source**:  The industry standard LNA topology using a source inductor to generate a real input impedance part ($50\Omega$) without adding noise.
    * **Common-Gate (CG)**: Broad-band input matching ($1/g_m$) often used for wideband applications.
    * **Resistive Feedback (Shunt-Shunt)**: For wideband matching at the cost of Noise Figure.
* **Rule**: The circuit is an **RF SISO Block**.
    * **Condition:** Must contain RF matching components (inductors, T-coils, matching capacitors) or be intended for $50\Omega$ environments.
    * **Strict Exclusion:** If the circuit performs Single-to-Differential conversion (Active Balun), it is **Class 20**. Class 38 output is always single-ended.