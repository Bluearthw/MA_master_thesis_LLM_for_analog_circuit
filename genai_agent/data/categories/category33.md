### 33. Tunable Active-RC Filters
A filter circuit where the frequency response is controlled by an analog voltage or current. It uses active devices (transistors) operating as variable resistors or capacitors.
*   **Ports**:
    *   **Required**: One signal input (`Vin`/`VIN1`), one signal output (`Vout`/`VOUT1`).
    *   **Required**: At least one analog control port (`Vctrl`/`VB1`) for tuning the filter characteristics.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply an AC voltage source to the input. Perform a DC sweep on the control port.
    *   **Measurements**:
        *   AC analysis at different control voltage settings to plot the transfer function (gain and phase vs. frequency) and show the tuning of the cutoff frequency.
        *   Transient analysis with a step input to measure settling time and verify that the time constant changes with the control voltage.
*   **Rule**: The circuit must have a signal input and output, and its primary function must be frequency filtering. It must use at least one active device as a tunable resistive or capacitive element, controlled by a dedicated analog control port. This distinguishes it from passive filters (Class 34), which are not tunable, and from amplifiers with incidental filtering characteristics (e.g., Classes 1 or 7), where the primary goal is gain.