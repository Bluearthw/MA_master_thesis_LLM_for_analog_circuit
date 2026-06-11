### 30. Current Comparators
A circuit that compares two analog input currents and produces a digital output indicating which is larger.
*   **Ports**:
    *   **Required**: At least two analog current inputs, one for the signal (e.g., `Iin`/`IIN1`) and one for the reference (e.g., `Iref`/`IB1`).
    *   **Required**: At least one digital logic-level voltage output (e.g., `Vout`/`VOUT1`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a constant DC current source to one input (the reference) and a slow-ramping DC current source to the other input that sweeps across the reference level.
    *   **Measurements**:
        *   **DC Transfer Curve / Hysteresis**: Perform a DC or transient analysis to plot the output voltage vs. the input current. Measure the input switching thresholds for rising and falling input currents to determine any hysteresis.
        *   **Input Offset Current**: The differential input current required to make the output switch state.
        *   **Propagation Delay**: Perform a transient analysis with a step in the input current (with a defined overdrive current) to measure the time from the input crossing the reference threshold to the output reaching 50% of its final value.
*   **Rule**: The circuit must take at least one analog current signal input and produce a binary, digital-level voltage output based on comparing that input to a reference current level. This distinguishes it from voltage comparators (Class 29), which have voltage inputs, and from current amplifiers (Class 12), which have a proportional analog current output.