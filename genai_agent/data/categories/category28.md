### 28. Switching-Mode RF Power Amplifiers (e.g., Class D, E, F)
An amplifier that uses its active device(s) as switches for high-efficiency RF power amplification, often for constant-envelope signals.
*   **Ports**:
    *   **Required**: One RF signal input, which can be single-ended (`RFin`/`VIN1`) or differential (`RFinp`/`RFinn`). The input is driven by a large-signal waveform (e.g., a square wave or the locking signal for an oscillator).
    *   **Required**: One RF signal output, which can be single-ended (`RFout`/`VOUT1`) or differential (`RFoutp`/`RFoutn`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a large-signal periodic input (e.g., square wave or pulsed sinusoid) at the desired operating frequency. The output must be terminated with the correct load impedance for which the amplifier was designed.
    *   **Measurements**:
        *   **Power Added Efficiency (PAE) and Drain Efficiency (DE)**: This is the primary metric, measured using Harmonic Balance or a long transient simulation.
        *   **Output Power**: The power delivered to the fundamental frequency component at the load.
        *   **Waveform Verification**: Transient analysis to inspect the drain voltage and current waveforms of the switching transistor to verify optimal switching conditions (e.g., Zero Voltage Switching (ZVS) or Zero Current Switching (ZCS)).
        *   **Device Voltage Stress**: The peak voltage across the main switching device, a critical reliability metric.
        *   **Harmonic Content/Suppression**: The power level of harmonics at the output, measured with PSS/Harmonic Balance.
*   **Topologies**: Includes **Class E** amplifiers (which use a specific load network with an RF choke and shunt capacitor to shape waveforms for ZVS and ZVDS), **Class D** amplifiers (which use a pair of switches in a push-pull or bridge configuration), and **Class F** amplifiers (which use resonant networks to shape drain voltage/current into square/half-sine waves). This class also covers **injection-locked power amplifiers (ILPAs)**, where a switching oscillator is locked to an input signal's phase, allowing for high-efficiency amplification of phase-modulated signals.
*   **Rule**: The circuit must be an RF power amplifier where the active device operates as a switch (driven into cutoff and triode regions), not as a linearly controlled current source. The input is a large-signal drive, and the primary characterization focuses on efficiency and output power, rather than small-signal metrics like S-parameters or linearity metrics like IIP3. This distinguishes it from linear/quasi-linear PAs (Classes 1 and 20).