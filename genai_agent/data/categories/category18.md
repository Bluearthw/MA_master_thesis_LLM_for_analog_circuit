### 18. ESD Protection Circuits
Passive networks designed to protect sensitive internal circuitry from high-voltage electrostatic discharge events by clamping voltages and shunting high currents.
*   **Ports**:
    *   **Required**: An external port to be protected (`PIN`/`VIN1`) and an internal protected port (`POUT`/`VOUT1`). The circuit is connected between these two ports and referenced to the supply rails (`VDD`, `VSS`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: High-current pulses emulating ESD events, typically using Transmission Line Pulsing (TLP) to generate an I-V curve. Standard ESD models like the Human Body Model (HBM) can be used for transient verification.
    *   **Measurements**:
        *   **I-V Clamping Curve (TLP)**: Plot the clamping voltage at the protected node (`POUT`) versus the injected ESD current at the external port (`PIN`).
        *   **Failure Current (`It2`)**: The peak current the device can withstand before permanent damage, determined from the TLP curve.
        *   **Transient Clamping Voltage**: The peak voltage reached at the protected node during a specific ESD event (e.g., HBM pulse).
        *   **Impact on Signal Integrity**: S-parameter analysis (`S21`, `S11`) to measure insertion loss and return loss during normal, small-signal operation.
*   **Rule**: The circuit must be a passive or semi-passive network (typically diodes, resistors, SCRs, or GG-NMOS) with an input and output. Its primary function is to provide a low-impedance path to the supply rails when the input voltage exceeds the normal operating range, and it is characterized by its response to high-voltage/high-current stress tests. This distinguishes it from a passive filter (Class 11), which is characterized by its linear frequency response.