### 34. Passive Filters and Attenuators
A network composed entirely of passive components (R, L, C) designed to shape the frequency content of a signal or provide a fixed level of attenuation.
*   **Ports**:
    *   **Required**: One signal voltage input (e.g., `Vin`/`VIN1`).
    *   **Required**: One signal voltage output (e.g., `Vout`/`VOUT1`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply an AC voltage source to the input.
    *   **Measurements**:
        *   **Frequency Response**: AC analysis to plot the transfer function (gain and phase vs. frequency) to characterize it as low-pass, high-pass, band-pass, etc., and find cutoff frequencies.
        *   **S-parameters**: For RF applications, measure insertion loss (`S21`) and return loss (`S11`, `S22`).
        *   **Transient Response**: Transient analysis with a step or pulse input to measure the time-domain characteristics like rise time, settling time, and overshoot.
        *   **Input/Output Impedance**: AC analysis to measure the impedance looking into the input and output ports.
*   **Topologies**: Includes simple **RC, RL, LC, RLC** networks configured as low-pass, high-pass, band-pass, or band-stop filters. Also includes purely resistive attenuator networks (**Pi or T networks**) and **compensated attenuators** (as seen in oscilloscope probes) that use capacitors to achieve a flat frequency response.
*   **Rule**: The circuit must be a two-port network composed only of passive R, L, and C components. Its primary function is to modify the amplitude and/or phase of a signal in a frequency-dependent (filter) or frequency-independent (attenuator) manner. This distinguishes it from active filters (which contain amplifiers), tunable filters (Class 33, which have a control port), and ESD protection circuits (Class 18, characterized by non-linear, high-voltage behavior).