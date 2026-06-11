### 2. Oscillators and Voltage-Controlled Oscillators (VCOs)
A circuit that generates a periodic output signal (e.g., sine wave, square wave) without a periodic input. The frequency can be fixed or controlled by an analog voltage (VCO).
*   **Ports**:
    *   **Required**: One or more signal outputs, which can be single-ended (e.g., `Vout`/`VOUT1`) or differential (e.g., `Voutp`/`VOUT1`, `Voutn`/`VOUT2`). Multi-stage oscillators may provide multiple outputs at different phases (e.g., quadrature outputs).
    *   **Optional**: One or more analog control voltage inputs (e.g., `Vctrl`/`VCONT1`, `VCONT2`) for tuning the oscillation frequency (for VCOs).
*   **Stimuli/Measurements**:
    *   **Stimuli**: For VCOs, apply a DC sweep to the `Vctrl` input. For free-running oscillators, no signal input is needed. A transient kick (e.g., an `ic` initial condition or a short current pulse) might be needed to start oscillation in simulation.
    *   **Measurements**:
        *   **Oscillation Frequency**: Measured from transient analysis or PSS (Periodic Steady-State) analysis.
        *   **Tuning Range & Gain (for VCOs)**: Plot the output frequency versus the control voltage. The slope of this curve is the VCO gain (`K_O` in Hz/V or rad/s/V).
        *   **Phase Noise**: PSS/PNOISE analysis to measure the spectral purity of the output signal. This is a critical metric for oscillators.
        *   **Output Swing / Amplitude**: The peak-to-peak voltage of the output waveform.
        *   **Power Consumption**: And its variation across the tuning range.
*   **Topologies**: Includes **LC-tank oscillators** (e.g., **Colpitts, Hartley, cross-coupled LC-VCOs**), **ring oscillators** (made of an odd number of single-ended inverters or a chain of differential delay cells), and **relaxation oscillators** (e.g., based on charging/discharging a capacitor with a Schmitt trigger).
*   **Rule**: The circuit's primary function must be to generate a periodic signal autonomously. If it has an analog control input for frequency, it is a VCO. This distinguishes it from amplifiers (which process an input signal), latches (which store a DC state), negative impedance converters (Class 10, which are often just the core active part of a tank oscillator), and complete PLLs (Class 17, which are feedback systems containing an oscillator).