### 7. Differential-to-Single-Ended Amplifiers (Operational Amplifiers / DISO)
An amplifier designed to amplify the voltage difference between two inputs and convert it into a single-ended output voltage relative to ground. This is the classic "Operational Amplifier" configuration, widely used for feedback loops where a single control signal is required.

* **Ports**:
    * **Required**: A pair of **differential voltage inputs** (e.g., `Vinp`/`PLUS`, `Vinn`/`MINUS`).
    * **Required**: Exactly **one signal voltage output** (e.g., `Vout`/`OUT`).
    * **Optional**: Control voltage inputs for frequency compensation tuning (e.g., `VCONT`) or power-down/enable pins.
* **Stimuli/Measurements**:
    * **Stimuli**: Apply a differential AC signal ($V_{dm}$) to measure gain, and a common-mode DC sweep ($V_{cm}$) to check input range.
    * **Measurements**:
        * **Open-Loop Voltage Gain ($A_{vol}$)**: AC magnitude and phase response ($V_{out} / V_{dm}$).
        * **Input Common-Mode Range (ICMR)**: The range of DC input voltages over which the input differential pair remains in saturation and the circuit functions correctly.
        * **Common-Mode Rejection Ratio (CMRR)**: The ratio of differential gain to common-mode gain. This is a critical metric for this class, quantifying how well the circuit rejects noise present on both inputs.
        * **Power Supply Rejection Ratio (PSRR)**: AC analysis of the supply rail.
        * **Output Swing**: The linear voltage range of the single-ended output (limited by supply rails and saturation voltages of the output transistors).
        * **Slew Rate**: Transient analysis with a large-signal step to measure the maximum rate of change of the output voltage.
* **Topologies**:
    * **Conversion Mechanism**: The defining feature of this class is the conversion from differential to single-ended. This is typically achieved using a **Current Mirror Active Load** (e.g., a "Five-Transistor" topology) or a specific summing stage.
    * **Input Stages**: Includes **Differential Pairs** (MOSFET, BJT, Darlington) using resistive or active loads. Techniques like **source/emitter degeneration** are used for linearity. Input stages may be **PMOS/PNP** (for low input ranges), **NMOS/NPN** (for high input ranges), or **Rail-to-Rail** (using parallel complementary pairs).
    * **Gain Stages**: Can be single-stage (e.g., Telescopic or Folded Cascode with a single-ended output branch) or multi-stage (e.g., the classic **Two-Stage Miller Op-Amp**). The two-stage design typically consists of a differential first stage driving a Common-Source second stage.
    * **Frequency Compensation**: Multi-stage designs often require internal compensation, such as **Miller Compensation** (splitting the poles) or **Feed-Forward** paths.
* **Rule**: The circuit must have a **Differential Input** pair and a **Single-Ended Output**. Its primary function is voltage amplification ($V_{out} \approx A \cdot (V_{inp} - V_{inn})$).
    * **Key Indicator**: Look for a differential pair where one side drives a current mirror that "turns around" the current to sum it with the other side at the output node.