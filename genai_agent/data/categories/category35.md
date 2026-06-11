### 35. Active Inductors / Gyrators
An active circuit that uses transistors to synthesize a frequency-dependent impedance that emulates an inductor.
*   **Ports**:
    *   **Required**: One or two signal ports across which the inductive impedance is presented. For a one-port implementation, this is a single terminal (e.g., `IN`/`IB1`) referenced to ground.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply an AC test source (voltage or current) to the signal port(s). The circuit must be biased into its active region, typically with a DC current source connected to the signal port.
    *   **Measurements**:
        *   **Impedance vs. Frequency**: AC analysis to plot the real and imaginary parts of the input impedance (`Zin`) versus frequency.
        *   **Equivalent Inductance (`L_eq`)**: Calculated from the imaginary part of the impedance (`imag(Zin) / (2*pi*f)`) in the operating frequency range.
        *   **Quality Factor (Q)**: Calculated from the ratio of the imaginary to the real part of the impedance (`imag(Zin) / real(Zin)`).
*   **Topologies**: Includes **gyrator-based** circuits that use two transconductors in a feedback loop to convert a capacitance into an inductance. A common single-transistor implementation of this principle uses a single active device to realize the gyrator.
*   **Rule**: The circuit must be a one-port or two-port active network whose primary function is to present a positive inductive impedance at its port(s). It is characterized by its Z-parameters, not by gain or other amplifier metrics. This distinguishes it from one-port negative impedance converters (Class 10), which generate a negative resistance, and from passive networks (Class 34).