### 26. Regenerative Frequency Dividers
Analog/RF circuits that perform frequency division by locking to a sub-harmonic of an input signal, typically using a mixer and filter in a feedback loop.
*   **Ports**:
    *   **Required**: One high-frequency clock input, which can be single-ended or differential (e.g., `CLK_IN`/`VIN1`, `VIN2`).
    *   **Required**: One frequency-divided clock output, which can be single-ended or differential (e.g., `CLK_OUT`/`VOUT1`, `VOUT2`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a high-frequency sinusoidal or square-wave clock to the input.
    *   **Measurements**:
        *   **Operating Frequency Range (Lock Range)**: Sweep the input clock frequency and check the output for correct and stable division. This determines the range over which the divider operates.
        *   **Functionality Verification**: Perform a transient analysis to confirm the output frequency is `f_in / N` (e.g., `f_in / 2`).
        *   **Phase Noise**: PSS/PNOISE analysis to measure the phase noise of the output clock relative to the input.
        *   **Power Consumption**.
*   **Topologies**: Includes **Miller dividers**, which use a mixer (active or passive) and a filter in a regenerative feedback loop. Also includes **Injection-Locked Oscillators (ILOs)**, where a free-running oscillator is injected with a signal at a multiple of its oscillation frequency, forcing it to lock.
*   **Rule**: The circuit must perform frequency division using an analog regenerative mechanism (mixing/feedback or injection locking). This distinguishes it from digital logic-based dividers (Class 25), which use clocked latches or flip-flops to achieve division.