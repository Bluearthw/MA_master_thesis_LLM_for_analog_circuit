### 4. Transimpedance Amplifiers (TIA)
An amplifier that converts an input current signal into a proportional output voltage signal. Can be single-ended or differential.
*   **Ports**:
    *   **Required**: At least one signal current input (e.g., single-ended `Iin`/`IIN1` or differential `Iinp`/`VIN1`, `Iinn`/`VIN2`).
    *   **Required**: At least one signal voltage output (e.g., single-ended `Vout`/`VOUT1` or differential `Voutp`/`VOUT1`, `Voutn` / `VOUT2`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply an AC current source (or differential AC current sources) superimposed on a DC bias current to the input(s).
    *   **Measurements**:
        *   **Transimpedance Gain (`R_T = Vout / Iin`)**: AC analysis to measure the gain (single-ended or differential) and -3dB bandwidth.
        *   **Input/Output Impedance**: AC analysis. A TIA is characterized by low input impedance. The output impedance depends on the topology: classic shunt-shunt feedback TIAs have low output impedance, while open-loop topologies like Common-Gate or Regulated Cascode have high output impedance. For differential designs, measure differential and common-mode impedance.
        *   **Input/Output Swing**: DC sweep of the input current to determine the linear operating range of the output voltage.
        *   **Slew Rate & Settling Time**: Transient analysis with a step in the input current.
        *   **Noise**: Analysis to measure the input-referred current noise density.
*   **Topologies**:
    *   **Single-ended**: The classic topology is a high-gain voltage amplifier with a feedback element (e.g., a **feedback resistor** or an **active feedback transistor**) from the output to the input, creating a **shunt-shunt feedback** configuration. The forward amplifier can be single or multi-stage (e.g., a **two-stage common-source amplifier**). Other common topologies are open-loop and rely on a low-impedance input stage. A prominent example is the **common-gate (CG)** amplifier, which directly converts the input current to a voltage at its high-impedance drain node when paired with an active load. To achieve higher gain, this CG stage can be followed by one or more voltage gain stages (e.g., a common-source stage). More advanced open-loop designs include **regulated cascode (RGC)** TIAs, which use a local feedback amplifier to achieve extremely low input impedance.
    *   **Differential**: A fully differential voltage amplifier (e.g., a **differential pair** or a **fully differential op-amp**) with parallel feedback resistors from each output to the corresponding input.
*   **Rule**: The circuit's primary function must be to convert a current signal at its input(s) to a voltage signal at its output(s). This is identified by low-impedance current-sinking input port(s) and voltage-sourcing output port(s). This distinguishes it from voltage amplifiers (Classes 1 and 7, V-to-V), transconductance amplifiers (Class 11, V-to-I), and current amplifiers (Class 12, I-to-I).