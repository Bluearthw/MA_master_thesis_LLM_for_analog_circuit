### 14. Switched-Capacitor (SC) Biasing Circuits and References
Generates a stable DC bias current or voltage whose value is set by capacitors and a clock frequency, making it largely independent of supply voltage, temperature, and process parameters.
*   **Ports**:
    *   **Required**: One or more clock inputs (e.g., `VCLK1`, `VCLK2`).
    *   **Required**: One or more DC bias outputs, which can be a mirrored current (`Iout`) or a bias voltage (`Vbias`/`VREF1`).
    *   **Optional**: One or more bias current inputs (e.g. `IB1`, `IB2`) for circuits like bandgap references.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Requires one or more periodic clock signals, often with non-overlapping phases.
    *   **Measurements**:
        *   DC operating point analysis (with clocks running in a PSS simulation) to find the nominal output current/voltage.
        *   DC sweep of the supply voltage (`VDD`) and clock frequency (`f_clk`) to measure line regulation and frequency dependence.
        *   DC sweep of temperature to measure the temperature coefficient (TC).
        *   Transient analysis with VDD ramping up to ensure proper start-up (these circuits often have a zero-current stable state and may require a dedicated startup circuit).
        *   Measure the transconductance (`gm`) of a designated transistor to verify the "constant-Gm" property.
*   **Topologies**: This class includes high-precision **switched-capacitor bandgap references**. In these circuits, a switched-capacitor network replaces traditional resistors for sampling BJT voltages and performing weighted summation. This approach offers precise voltage scaling based on capacitor ratios and often incorporates **Correlated Double Sampling (CDS)** to cancel the DC offset and low-frequency 1/f noise of the internal operational amplifier, leading to very high accuracy.
*   **Rule**: The circuit must generate a DC bias current or voltage and *must* require one or more clock inputs for its core operation, typically using a switched-capacitor network as a reference element. This distinguishes it from DC-only references (Class 6) and bias generators (Class 9).