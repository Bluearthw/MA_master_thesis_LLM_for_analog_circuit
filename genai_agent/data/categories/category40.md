### 40. Fully Differential Amplifiers (DIDO) 
An amplifier that amplifies the difference between two inputs and produces a differential output (the difference between two output nodes). These circuits maintain the signal in the differential domain throughout, offering superior power supply rejection, double the output swing, and cancellation of even-order harmonics compared to single-ended outputs.

* **Ports**:
    * **Required**: A pair of **differential voltage inputs** (e.g., `Vinp`/`IN+`, `Vinn`/`IN-`).
    * **Required**: A pair of **differential signal outputs** (e.g., `Voutp`/`OUT+`, `Voutn`/`OUT-`).
    * **Required (System)**: Almost all fully differential amplifiers require a mechanism to set the output Common-Mode (CM) level. This usually appears as:
        * A **CMFB Control Input** (`Vcm_ctrl`) if the feedback loop is external.
        * A **CM Reference Input** (`Vcm_ref` / `VVOCM`) if the feedback loop is internal.
    * **Optional**: Clock inputs (`VCLK`) if the CMFB is switched-capacitor based.
* **Stimuli/Measurements**:
    * **Stimuli**: Apply balanced differential AC signals. It is crucial to simulate the CMFB loop (either by connecting the external loop or providing the correct `Vcm_ref`) to ensure the DC operating point is settled.
    * **Measurements**:
        * **Differential-Mode Gain ($A_{dm}$)**: AC analysis of $(V_{outp} - V_{outn}) / (V_{inp} - V_{inn})$.
        * **Common-Mode Gain ($A_{cm}$)**: The gain from a common-mode input to a common-mode output. Ideally close to zero or determined by the CMFB loop response.
        * **Output Balance**: Verification that $V_{outp}$ and $V_{outn}$ are 180° out of phase.
        * **CMFB Loop Stability**: Stability analysis (`stb`) performed specifically on the common-mode feedback loop to ensure the output DC level does not oscillate.
        * **Settling Time**: Measuring how fast the output differential voltage settles *and* how fast the common-mode level settles after a disturbance.
* **Topologies**:
    * **Core Structure**: Similar to single-ended designs but completely symmetrical. This includes **Fully Differential Folded Cascodes**, **Telescopic Cascodes**, and **Gain-Boosted** architectures.
    * **Common-Mode Feedback (CMFB)**: A unique requirement for this class. The CMFB circuit senses the output average $(V_{outp} + V_{outn})/2$ and adjusts the tail current or load bias to force it to equal `Vcm_ref`.
        * **Continuous-Time CMFB**: Uses resistive dividers (or triode transistors) and a separate error amplifier.
        * **Switched-Capacitor CMFB**: Uses clocked capacitors to sense and correct the level (common in discrete-time applications).
    * **Class AB Output**: Some fully differential amplifiers (especially drivers) use Class AB output stages to drive low-impedance loads while maintaining differential operation.
* **Rule**: The circuit must have a **Differential Input** pair and a **Differential Output** pair.
    * **Key Indicator**: The circuit is symmetrical from input to output. The presence of a "Common-Mode Feedback" network (or pins related to it) is the strongest signature of this class.
    * **Distinction from Class 16**: If the circuit uses a Switched-Capacitor network only for Common-Mode Feedback (CMFB) or Offset Cancellation, but the main signal path is continuous (transistor gates), it remains Class 40. It only becomes Class 16 if the main signal inputs are sampled by switches.