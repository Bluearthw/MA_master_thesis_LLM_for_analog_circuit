### 32. Rectifiers, Clippers, and Clamps
A circuit that produces an analog output by performing a non-linear waveshaping function, such as taking the absolute value (full-wave), clipping a portion (half-wave), or clamping the voltage of its analog input.
*   **Ports**:
    *   **Required**: One analog signal input (`Vin`/`VIN1`) and one analog signal output (`Vout`/`VOUT1`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a sinusoidal or triangular waveform to the input that swings both positive and negative.
    *   **Measurements**:
        *   **DC Transfer Curve**: DC sweep of the input voltage to plot the output voltage, verifying the `Vout = |Vin|` (full-wave) or `Vout = max(0, Vin)` (half-wave) or clamping characteristic.
        *   **Transient Analysis**: Apply a time-varying input to observe the rectified/clipped output waveform. Key metrics are crossover distortion (glitches near zero-crossing) and accuracy of the clamp/clip level.
        *   **Frequency Response**: Sweep the frequency of the input sinusoid to determine the maximum operating frequency for which the waveshaping remains accurate.
*   **Topologies**: Includes **passive implementations** using diodes and resistors to perform basic clipping or clamping. Also includes active **precision rectifiers** based on op-amps that reconfigure their feedback networks using diodes or analog switches to change between inverting and non-inverting configurations based on the input signal's polarity.
*   **Rule**: The circuit's primary function must be to perform a mathematical absolute value (full-wave) or a clipping/clamping (half-wave) operation on an analog input signal, producing a rectified analog output. This is identified by its characteristic non-linear 'V'-shaped (full-wave) or clipped (half-wave) DC transfer function, distinguishing it from linear amplifiers (Classes 1, 7, and 16) and comparators (Class 29, which have a digital output).