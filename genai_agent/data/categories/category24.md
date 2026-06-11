### 24. Digital Combinatorial Logic Gates
Digital circuits that perform a stateless, combinatorial logic function (e.g., AND, NAND, OR, XOR) on two or more input signals. This class covers high-speed logic families like Current-Mode Logic (CML).
*   **Ports**:
    *   **Required**: Two or more digital signal inputs, which can be single-ended or differential (e.g., `LOGICA1`/`LOGICA2`, `LOGICB1`/`LOGICB2`).
    *   **Required**: One or more digital signal outputs, which can be single-ended or differential (e.g., `VOUT1`, `VOUT2`).
    *   **Optional**: A tail current bias port (e.g., `IB1`) for current-steering logic families like CML.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply digital waveforms (pulses, clocks) to the inputs to cover the gate's truth table.
    *   **Measurements**:
        *   **Transient analysis** is the primary simulation.
        *   **Logical Function Verification**: Verify that the output corresponds to the correct logical combination of the inputs for all states.
        *   **Propagation Delay**: Measure the time from an input transition to the corresponding output transition (e.g., `t_pLH`, `t_pHL`).
        *   **Rise/Fall Times**: Measure the 10%-90% or 20%-80% transition times of the output signals.
        *   **Power Consumption**: Measure static and dynamic power consumption.
*   **Topologies**: Includes various digital logic families. Common implementations are based on **static CMOS logic** (using complementary pull-up PMOS and pull-down NMOS networks), **pass-gate logic** (using NMOS, PMOS, or transmission gates to steer signals, commonly used in clock multiplexers), or high-speed current-steering families like **Current-Mode Logic (CML)**. The functions implemented range from basic gates like **AND, NAND, OR, NOR, XOR** to more complex combinatorial blocks such as **multiplexers (MUX)** and decoders.
*   **Rule**: The circuit must implement a stateless, combinatorial logic function with at least two distinct logic inputs (e.g., A and B) and at least one logic output. This distinguishes it from clock buffers/inverters (Class 15), which typically have a single signal input path, and sequential logic like latches/flip-flops (Class 25).