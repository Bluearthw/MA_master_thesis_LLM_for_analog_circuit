### 10. Negative Impedance Converters / Oscillator Cores
Active circuits, often with an amplifier-like topology, designed to present a negative resistance or impedance at one of their ports. They are not complete oscillators but serve as the active core that provides the energy to sustain oscillation when connected to a resonant tank (e.g., an an LC circuit).
*   **Ports**:
    *   **Required**: At least one signal input port (e.g., `Vin`/`VIN1`) and one signal output port (e.g., `Vout`/`VOUT1`). The negative impedance is measured at one of these ports (usually the output).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a test AC voltage or current source at the port of interest (e.g., the output) while properly terminating the other port (e.g., grounding the input).
    *   **Measurements**:
        *   **Output Impedance**: AC analysis to plot the real and imaginary parts of the impedance versus frequency. The key metric is verifying a negative real part over the desired frequency range.
        *   **Stability Analysis**: Use stability analysis tools (e.g., `stb` in Spectre) to check for potential oscillation by calculating loop gain.
        *   **Oscillation Verification**: Transient analysis with a connected resonant tank (e.g., an LC load) to verify oscillation startup, frequency, and amplitude.
*   **Rule**: The circuit must be an active two-port network whose primary design purpose is to generate a negative impedance at one of its ports, typically to overcome losses in a resonator and create an oscillator. This is determined by its topology (e.g., specific feedback arrangements like the one provided) and characterization, which focuses on impedance rather than stable linear voltage gain (distinguishing it from Class 1).