### 31. Timing Circuits (e.g., 555 Timer)
A mixed-signal circuit that generates time delays (monstable mode) or oscillations (astable mode) based on the charging and discharging of an external RC network.
*   **Ports**:
    *   **Required**: At least two analog voltage inputs for timing control: a `Threshold` input (e.g., `VCONT1`) and a `Trigger` input (e.g., `VCONT2`).
    *   **Required**: One digital logic-level output (`Vout`/`VOUT1`).
    *   **Optional**: A `Control Voltage` input (e.g., `VCONT5`) to access or override an internal reference voltage, a `Reset` input to force the output to a known state, and a `Discharge` output (often open-drain) to discharge the external timing capacitor.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Requires connection of an external RC network to the `Threshold`, `Trigger`, and `Discharge` pins to configure for astable (oscillator) or monostable (one-shot) operation.
    *   **Measurements (Transient Analysis)**:
        *   **Astable Mode**: Measure the frequency, period, and duty cycle of the output waveform.
        *   **Monostable Mode**: Apply a trigger pulse to the `Trigger` input and measure the resulting output pulse width.
        *   **Threshold and Trigger Voltage Levels**: Verify the exact input voltage levels that cause the output to switch states.
        *   **Output Voltage Levels (`V_OH`, `V_OL`)** and current drive capability.
*   **Rule**: The circuit must be a stateful block containing voltage comparators, a flip-flop, and an internal voltage reference. Its primary function is to produce time-based digital output signals controlled by analog voltage levels on dedicated 'Threshold' and 'Trigger' inputs, typically in conjunction with an external RC network. This distinguishes it from simple comparators (Class 29, which lack the internal state machine) and free-running oscillators (Class 2, which may not have this specific control structure).