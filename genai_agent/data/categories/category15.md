### 15. Clock Generation and Distribution Logic
Digital circuits that take one or more input clock signals and produce one or more output clock signals with specific timing relationships (e.g., buffered, inverted, delayed, non-overlapping phases).
*   **Ports**:
    *   **Required**: At least one clock input (e.g., `CLK_IN`, `VCLK2`, `VCLK3`) and at least one clock output (e.g., `CLK_OUT`, `VCLK1`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply periodic digital clock signals to the input(s).
    *   **Measurements**:
        *   **Transient analysis** is the primary simulation method.
        *   Measure propagation delay from input(s) to output(s).
        *   Measure rise time, fall time, and duty cycle of the output clocks.
        *   For multi-phase generators, measure the non-overlapping time between clock phases.
        *   Measure clock skew between different output branches.
*   **Rule**: The circuit must be composed of digital logic gates (inverters, buffers, pass gates, NAND/NOR, etc.) and its primary function must be to manipulate the timing or phase of a an clock signal. It is not an oscillator (does not self-oscillate) and its outputs are digital, not analog control levels. This distinguishes it from oscillators (Class 2) and PLL building blocks such as charge pumps (Class 23).