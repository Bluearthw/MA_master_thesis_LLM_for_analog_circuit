### 25. Clocked Sequential Logic (Latches, Flip-Flops, Frequency Dividers)
Digital circuits that store one or more bits of information and whose state transitions are controlled by one or more clock signals. This class includes frequency dividers, which are a common application of flip-flops.
*   **Ports**:
    *   **Required**: At least one clock input (e.g., `CLK`/`VCLK1`, can be differential).
    *   **Required**: One or more state outputs (e.g., `Q`, can be differential).
    *   **Optional**: One or more data inputs (e.g., `D`/`LOGICD1`, can be differential). For circuits like frequency dividers, the data input may be internally connected to an output and not exposed as a top-level port.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a periodic clock signal to the clock input(s). If data inputs are present, apply digital data waveforms synchronized to the clock.
    *   **Measurements (Transient Analysis)**:
        *   **For Flip-Flops/Latches**:
            *   **Setup Time**: Minimum time the data input must be stable *before* the active clock edge/level.
            *   **Hold Time**: Minimum time the data input must be stable *after* the active clock edge/level.
            *   **Clock-to-Q Delay (Propagation Delay)**: Time from the active clock edge to the corresponding change at the output.
        *   **For all types (including dividers)**:
            *   **Maximum Clock Frequency (`f_max`)**: The highest clock frequency at which the circuit operates correctly. For dividers, this means producing a stable, divided output.
            *   **Functionality Verification**: For dividers, verify that the output frequency is the input frequency divided by the expected ratio (e.g., 2).
*   **Topologies**: Includes level-sensitive **D-latches** (e.g., based on Current-Mode Logic or dynamic styles like **True Single-Phase Clocking (TSPC)**), edge-triggered **D-flip-flops** (often master-slave configurations), T-flip-flops (toggle), and **frequency dividers** (including programmable **dual-modulus prescalers**). A common implementation of a divide-by-2 circuit is a master-slave D-flip-flop with its inverted output fed back to its data input; this topology naturally provides **quadrature outputs** (90° phase shift) from the master and slave stages.
*   **Rule**: The circuit must be a digital block with clock inputs and state outputs, whose primary function is to sample and store data (or its own previous state) based on a clock signal. This distinguishes it from combinatorial logic (Class 24), which lacks memory, and simple unclocked bistable cells (Class 21), which are not controlled by a dynamic clock signal for data capture.