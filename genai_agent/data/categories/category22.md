### 22. Voltage-Controlled Variable Capacitors (Varactors)
A circuit that provides a voltage-tunable capacitance, typically used for frequency tuning in oscillators or filters.
*   **Ports**:
    *   **Required**: Two terminals across which the variable capacitance is presented (e.g., `Port1`/`IB1`, `Port2`/`VCONT1`).
    *   **Required**: An analog control voltage input (e.g., `Vctrl`). This control input may be one of the capacitor terminals (e.g., `Vctrl` is the same node as `Port2`).
    *   **Optional**: A bias current port (`Ibias`) may be required if the varactor includes an active biasing scheme. This bias port may be the same node as one of the capacitor terminals (e.g., `Ibias` is sourced into `Port1`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Sweep the DC control voltage (`Vctrl`) over its operating range. For circuits requiring a bias current, provide a constant DC current source.
    *   **Measurements**:
        *   **C-V Curve**: At each step of the control voltage sweep, perform an AC analysis (or S-parameter analysis) to extract the capacitance between the capacitor terminals. Plot the capacitance versus the control voltage.
        *   **Quality Factor (Q)**: From the same AC/SP analysis, calculate the quality factor (`Q = imag(Y)/real(Y)`) of the varactor across frequency and as a function of the control voltage.
*   **Topologies**: Includes single or parallel **MOS varactors** (often accumulation-mode for monotonic C-V curves) and reverse-biased PN junction diodes. May include an integrated active biasing network (e.g., diode-connected transistors) to set the DC operating point of the capacitor terminals.
*   **Rule**: The circuit's primary function must be to act as a capacitor whose value is controlled by a separate analog voltage input. It must have at least three terminals: two for the capacitance and one for the control voltage. This distinguishes it from fixed two-terminal passive impedance networks (Class 34).