### 17. Phase-Locked Loops (PLL)
A feedback control system that generates an output signal whose phase is locked to the phase of an input reference signal.
*   **Ports**:
    *   **Required**: A reference signal input (e.g., `REF_CLK`/`VIN1`) and one or more clock signal outputs (e.g., `CLK_OUT`/`VOUT1`, `VOUT2`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a periodic reference clock signal to the input.
    *   **Measurements**:
        *   **Transient analysis**: Apply a step in the input frequency to observe the locking process and measure the lock time.
        *   **Lock Range / Capture Range**: Sweep the input frequency to determine the frequency range over which the PLL can acquire and maintain phase lock.
        *   **Output Jitter / Phase Noise**: Measure the timing variations and spectral purity of the output clock using transient analysis (for jitter) or PSS/PNOISE analysis (for phase noise).
        *   **Reference Spurs**: Measure the magnitude of unwanted spectral components at offsets equal to the reference frequency in the output spectrum using PSS/Harmonic Balance analysis.
*   **Rule**: The circuit must be a complete closed-loop system containing a phase detector, a loop filter, and a voltage-controlled oscillator (VCO). Its primary function is to synchronize its output frequency and phase to a reference input signal. This distinguishes it from its individual components like free-running oscillators (Class 2) or standalone charge pump/phase detector blocks (Class 23).