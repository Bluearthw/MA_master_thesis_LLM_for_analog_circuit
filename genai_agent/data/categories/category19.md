### 19. Analog Adder / Subtractor / Combiner
An active circuit that combines (adds or subtracts) two or more input signals to produce a single output signal. This includes both baseband summing amplifiers and RF power combiners.
*   **Ports**:
    *   **Required**: At least two distinct signal inputs (e.g., `VinA`, `VinB`). These can be single-ended (e.g., `VIN1`, `VIN2`) or differential pairs.
    *   **Required**: One or more signal outputs (`Vout`), which can be single-ended (e.g., `VOUT1`, `VOUT2`) or differential. If multiple outputs are present, they typically carry the same combined signal.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply distinct AC signals to each input port. For RF combiners, these are typically high-frequency tones with a specific phase relationship.
    *   **Measurements**:
        *   **Transfer Function**: Perform AC or S-parameter analysis from each input to the output to verify the gain and bandwidth for each path.
        *   **Linearity (IMD)**: For baseband adders, apply multiple tones and measure intermodulation distortion.
        *   **Combining Efficiency/Power**: For RF power combiners, perform Harmonic Balance analysis to measure output power and efficiency as a function of the input signals' phase difference.
        *   **Transient Verification**: Apply signals to all inputs simultaneously and observe the output waveform to verify the combination.
*   **Topologies**: Includes op-amp based summing amplifiers and **transconductance-based summing amplifiers**, where multiple parallel input transconductors (e.g., common-source stages) have their output currents summed at a common node, which is then converted back to a voltage by a load or a subsequent gain stage. This class also includes **RF Power Combiners**, such as the output stage of an **outphasing (LINC) amplifier**, where two parallel, non-linear amplifier stages are current-summed at a common output node to reconstruct a linear, amplitude-modulated signal.
*   **Rule**: The circuit must have at least two distinct signal input ports and one signal output port. Its primary function must be to produce an output signal that is a combination (sum or difference) of the input signals. This distinguishes it from a standard amplifier (Classes 1, 7, or 16) which has only one primary signal input, and from a mixer (Class 3) which performs non-linear multiplication for frequency conversion.