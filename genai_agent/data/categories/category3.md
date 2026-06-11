### 3. RF Mixers
A circuit that performs frequency translation by multiplying a high-frequency RF signal with a local oscillator (LO) signal to produce a lower-frequency intermediate frequency (IF) or baseband signal (downconversion), or a higher-frequency signal (upconversion).
*   **Ports**:
    *   **Required**: At least one RF signal input (e.g., `RFin`/`VIN1`, can be single-ended or differential).
    *   **Required**: At least one LO signal input (e.g., `LOin`/`VCLK1`, `VCLK2`, can be single-ended or differential and is often a large-signal clock).
    *   **Required**: At least one IF/baseband signal output (e.g., `IFout`/`VOUT1`, can be single-ended or differential).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a sinusoidal RF signal to the `RFin` port and a large-signal periodic waveform (sinusoid or square wave) at the LO frequency to the `LOin` port.
    *   **Measurements**:
        *   **Conversion Gain (CG)**: The ratio of the desired IF output power/voltage to the RF input power/voltage. Measured using Harmonic Balance or PSS analysis.
        *   **Linearity (IIP3, P1dB)**: Characterizes distortion using a two-tone test at the RF input.
        *   **Noise Figure (NF)**: Measures the noise added by the mixer (single-sideband or double-sideband).
        *   **Port-to-Port Isolation**: S-parameter measurements (e.g., LO-to-RF, RF-to-IF) to quantify signal leakage.
*   **Topologies**: Includes active mixers based on non-linear transconductance (e.g., the **Gilbert Cell**), passive mixers using diode rings or FET switches, and **sampling mixers**. The sampling mixer topology, often implemented in **BiCMOS**, uses a transconductance stage to convert the RF voltage to a current, which is then sampled by a switched-capacitor network driven by the LO. This periodic sampling performs the frequency downconversion. The transconductance stage may be a differential pair with emitter degeneration for linearity, feeding into a **folded cascode** structure to drive the sampling switches.
*   **Rule**: The circuit's primary function must be frequency translation, identified by the presence of three distinct signal ports: RF input, LO input, and IF output. This distinguishes it from analog multipliers (Class 8), where both inputs are typically small-signal analog signals, and from amplifiers (Classes 1, 7), which lack a dedicated LO input and do not perform frequency conversion.