### 27. Digital-to-Analog Converters (DAC)
A circuit that converts a multi-bit digital input word into a proportional analog output signal (current or voltage).
*   **Ports**:
    *   **Required**: Multiple digital input ports representing the input code (e.g., `D0`, `D1`, ... or `VCONT1`, `VCONT2`, `VCONT3`).
    *   **Required**: One analog output port, which can be a current (`Iout`/`IOUT1`) or a voltage (`Vout`).
    *   **Optional**: A reference input, which can be a current (`Iref`/`IREF1`) for scaling a current-steering DAC, or a voltage (`Vref`) for resistor-string or switched-capacitor DACs.
    *   **Optional**: A clock input (`CLK`) for latched or pipelined DACs.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a sequence of digital codes to the inputs, typically ramping from all '0's to all '1's.
    *   **Measurements**:
        *   **Static Linearity (DC Analysis)**: Perform a DC analysis at each input code and measure the corresponding analog output.
        *   **Differential Non-Linerity (DNL)**: The deviation in step size between adjacent codes from the ideal step size (LSB).
        *   **Integral Non-Linerity (INL)**: The maximum deviation of the actual transfer curve from an ideal straight line.
        *   **Gain Error & Offset Error**: Deviations in the slope and y-intercept of the best-fit line through the transfer curve.
        *   **Dynamic Performance (for high-speed DACs)**:
            *   **Settling Time**: Time for the output to settle to within a certain error band after a code transition.
            *   **Spurious-Free Dynamic Range (SFDR)**: Measured by applying a digital sine wave to the input and analyzing the output spectrum for the largest spurious tone relative to the fundamental.
*   **Topologies**: Includes **current-steering DACs** (which use an array of switched current sources), R-2R ladders, resistor-string DACs, and charge-redistribution (switched-capacitor) DACs.
*   **Rule**: The circuit must have a multi-bit digital input (two or more control bits) and a single analog output (current or voltage). Its primary function must be to convert the digital code into a proportional analog level. This distinguishes it from simple single-bit current-steering cells (Class 12).