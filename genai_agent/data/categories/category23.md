### 23. Charge Pump
A circuit that converts digital "Up" and "Down" control pulses into a current that is sourced or sunk from an output node. It is typically used with an external or integrated loop filter to generate an analog control voltage.
*   **Ports**:
    *   **Required**: Two digital control inputs, one for "Up" (e.g., `LOGICQA1`/`UP`/`VCONT2`) and one for "Down" (e.g., `LOGICQB1`/`DN`/`VCONT4`).
    *   **Required**: One analog output port (e.g., `Iout`/`net20`) from which current is sourced/sunk. If a loop filter is integrated, this port provides the output voltage.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply periodic, digital pulse trains to the `UP` and `DN` inputs. If the circuit is a standalone charge pump, an external load (typically a capacitor representing the loop filter) must be connected to the output for transient analysis.
    *   **Measurements**:
        *   **Current Matching**: Apply long, separate pulses to the `UP` and `DN` inputs and measure the output current directly (in DC analysis) or the output voltage slew rate (`dV/dt`) across the load capacitor (in transient analysis) to verify that the sourced and sinked currents are equal.
        *   **Output Ripple**: Apply simultaneous, narrow, and identical pulses to both inputs (simulating a locked PFD state) and measure the peak-to-peak voltage variation on the output node (with load capacitor).
        *   **Voltage Compliance Range**: Sweep the DC voltage of the output node and measure the output current to determine the voltage range over which the charge pump currents remain matched and within specification.
*   **Rule**: The circuit must have two digital inputs corresponding to "Up" and "Down" commands and a single analog output that sources or sinks current based on these commands. This class covers both standalone charge pumps and those with an integrated loop filter. It is distinguished from complete PLL blocks (Class 17), which take reference and feedback clocks directly rather than discrete Up/Down pulses.