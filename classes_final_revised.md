### 1. Single-Ended Baseband Voltage Amplifiers (Linear Gain Stages)
A fundamental gain block intended for signal conditioning, typically operating in the "small-signal" regime where linearity is assumed and crossover distortion is negligible. These circuits prioritize voltage gain accuracy, bandwidth, and feedback stability.

* **Ports:**
    * **Required:** **Exactly one** signal voltage input (High Impedance typical). *If a second signal input exists, it is Class 7 or 40.*
    * **Required:** Single voltage output (Medium/Low Impedance).
    * **Note:** Unlike RF amps, input impedance matching is rarely required; the focus is on voltage bridging ($Z_{in} \gg Z_{source}$).
* **Stimuli/Measurements:**
    * **Stimuli:** Small-signal AC voltage source; DC bias voltage.
    * **Measurements:**
        * **Voltage Gain ($A_v$) & Phase:** AC analysis to determine DC gain and the -3dB corner frequency.
        * **Stability (PM/GM):** **Critical.** Analysis of Phase Margin and Gain Margin to ensure the amplifier does not oscillate when placed in a feedback loop.
        * **PSRR:** AC analysis of supply rejection (often critical in baseband precision circuits). *(Note: CMRR is not applicable here as there is no accessible differential input pair).*
        * **Input-Referred Noise:** Voltage noise density ($nV/\sqrt{Hz}$) integration over the bandwidth.
        * **Slew Rate:** Transient analysis with a step response (strictly for settling time, not distortion).
* **Topologies:**
    * **Fundamental Stages:** Common-Source (CS), Common-Emitter (CE), Cascode, Telescopic Cascode, Folded Cascode.
    * **Multi-Stage:** Operational Amplifiers (Op-Amps) in open loop or fixed feedback configurations, OTA (Operational Transconductance Amplifiers).
    * **Internal Differential Structures:** 

 Includes circuits that use a **differential input pair internally** (e.g., an Op-Amp with feedback resistors or a self-biased reference on the inverting node) but **do not expose the second input** as a top-level port.
    * **Active Loads:** Current mirrors, active inductor loads (for bandwidth extension without RF tuning).
* **Rule:** The circuit is a **linear gain block** with a **Single-Input/Single-Output (SISO)** interface.
    * It is disqualified if it includes inductive source degeneration (indicates LNA).
    * It is disqualified if it relies on complementary switching devices for high-current output (indicates Push-Pull/Class AB).

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

### 3. RF Mixers
A circuit that performs frequency translation by multiplying a high-frequency RF signal with a local oscillator (LO) signal to produce a lower-frequency intermediate frequency (IF) or baseband signal (downconversion), or a higher-frequency signal (upconversion).
*   **Ports**:
    *   **Required**: At least one RF signal input (e.g., `RFin`/`VIN1`, can be single-ended or differential).
    *   **Required**: At least one LO signal input (e.g., `LOin`/`VCLK1`, `VCLK2`, can be single-ended or differential and is often a large-signal clock).
    *   **Required**: At least one IF/baseband signal output (e.g., `IFout`/`VOUT1`, can be single-ended or differential).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a sinusoidal RF signal to the `RFin` port and a large-signal periodic waveform (sinusoid or square wave) at the LO frequency to the `LOin` port.
    *   **Measurements**:
        *   **Conversion Gain (CG)**: The ratio of the desired IF output power/voltage to the RF input power/voltage. Measured using Harmonic Balance or PSS analysis.
        *   **Linearity (IIP3, P1dB)**: Characterizes distortion using a two-tone test at the RF input.
        *   **Noise Figure (NF)**: Measures the noise added by the mixer (single-sideband or double-sideband).
        *   **Port-to-Port Isolation**: S-parameter measurements (e.g., LO-to-RF, RF-to-IF) to quantify signal leakage.
*   **Topologies**: Includes active mixers based on non-linear transconductance (e.g., the **Gilbert Cell**), passive mixers using diode rings or FET switches, and **sampling mixers**. The sampling mixer topology, often implemented in **BiCMOS**, uses a transconductance stage to convert the RF voltage to a current, which is then sampled by a switched-capacitor network driven by the LO. This periodic sampling performs the frequency downconversion. The transconductance stage may be a differential pair with emitter degeneration for linearity, feeding into a **folded cascode** structure to drive the sampling switches.
*   **Rule**: The circuit's primary function must be frequency translation, identified by the presence of three distinct signal ports: RF input, LO input, and IF output. This distinguishes it from analog multipliers (Class 8), where both inputs are typically small-signal analog signals, and from amplifiers (Classes 1, 7), which lack a dedicated LO input and do not perform frequency conversion.

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

### 5. Sample-and-Hold / Track-and-Hold Circuits
A circuit that samples a continuous-time analog input signal at a specific time (controlled by a clock) and holds that value on a capacitor.
*   **Ports**:
    *   **Required**: One analog signal input, which can be single-ended (`Vin`/`VIN1`) or differential (`Vinp`/`VIN1`, `Vinn`/`VIN2`).
    *   **Required**: One analog signal output, which can be single-ended (`Vout`/`VOUT1`) or differential (`Voutp`/`VOUT1`, `Voutn`/`VOUT2`).
    *   **Required**: One or more clock inputs (`Vclk`/`VCLK1`, `VTRACK1`, `VHOLD1`) to control the sample/track and hold phases.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply an analog waveform (e.g., sine wave or ramp) to the input and a periodic digital clock signal to the clock input.
    *   **Measurements**:
        *   **Acquisition Time**: In transient analysis, the time required during the track/sample phase for the held voltage to settle within a specified error band of the input voltage.
        *   **Hold Step (Pedestal Error)**: The voltage error introduced at the output when transitioning from track to hold mode, caused by **charge injection** from the switch and **clock feedthrough** via parasitic capacitance.
        *   **Droop Rate**: The rate at which the output voltage changes during the hold phase due to leakage currents discharging the hold capacitor.
        *   **Aperture Jitter/Uncertainty**: The time variation in the exact sampling instant, which translates voltage-domain noise for high-frequency inputs. It is affected by both clock jitter and signal-dependent switch delays.
        *   **Signal Feedthrough**: The amount of input signal that couples to the output during the hold phase.
        *   **Distortion (SFDR, THD)**: Non-linearity caused by signal-dependent charge injection and variations in the switch's on-resistance.
*   **Topologies**: Includes the basic **MOS switch and hold capacitor** configuration, as well as **diode bridge** samplers. The diode bridge switch is often turned on and off not by a direct clock signal, but by **switched current sources** that forward- or reverse-bias the diodes, a technique that improves signal-independent clock feedthrough. These core sampling structures are almost always followed by an **output buffer** (e.g., a source follower or a complete operational amplifier in a unity-gain configuration) to provide drive capability without disturbing the held voltage. More advanced designs use techniques to mitigate non-idealities, such as **dummy switches** for charge injection cancellation, **bootstrapped switches** for constant on-resistance over the input voltage range, and **fully differential architectures** for improved common-mode noise rejection. High-performance implementations may place the switch and capacitor within the feedback loop of a high-gain operational amplifier. This core amplifier is often a high-performance, multi-stage design (e.g., a **telescopic or folded-cascode OTA** followed by an output buffer), which forces the output to track the input with high precision. Such op-amp-based topologies can also be configured to cancel the op-amp's own offset.
*   **Rule**: The circuit's primary function is to convert a continuous-time analog signal into a discrete-time analog signal by sampling its value at clock-defined instants. The output is a staircase-like approximation of the input. This distinguishes it from SC amplifiers/integrators (Class 16), which perform a more complex mathematical operation (e.g., gain > 1, integration) on the sampled signal.

### 6. DC Voltage References (e.g., Bandgap)
A circuit that generates a precise and stable DC output voltage, designed to be largely independent of power supply, temperature, and process variations.
*   **Ports**:
    *   **Required**: One low-impedance DC voltage output (`Vout`/`VREF`/`VOUT1`/`VREF1`).
    *   **Optional**: An enable/shutdown input (`EN`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: No signal input required. The circuit is self-referencing.
    *   **Measurements**:
        *   **DC Output Voltage**: The nominal output voltage at a reference temperature and supply.
        *   **Line Regulation**: DC sweep of the supply voltage (`VDD`) to measure the change in output voltage (`ΔVout / ΔVdd`).
        *   **Load Regulation**: DC sweep of a load current drawn from the output to measure the change in output voltage (`ΔVout / ΔIload`).
        *   **Temperature Coefficient (TC)**: DC sweep of temperature to plot the output voltage and calculate its drift (in ppm/°C).
        *   **Power Supply Rejection Ratio (PSRR)**: AC analysis on the supply rail to measure the rejection of supply noise to the output.
        *   **Startup Behavior**: Transient analysis with VDD ramping up to ensure the circuit starts correctly and does not settle in an undesired stable state (e.g., zero-current).
        *   **Output Noise**: Noise analysis to measure the integrated output voltage noise over a specified bandwidth.
*   **Topologies**: Includes simple, self-biasing references such as a **series stack of diode-connected transistors** or the **VBE-multiplier reference**, which uses a transistor and a resistive feedback network to generate an output voltage that is a multiple of its base-emitter voltage (`V_BE` or `V_EB`). While these simple topologies can have good supply rejection, they are not temperature compensated and exhibit CTAT (Complementary to Absolute Temperature) behavior. The most common high-performance topology is the **Bandgap Reference**, which cancels the temperature dependencies of a BJT's base-emitter voltage (`V_BE`, negative TC) and a thermal voltage (`V_T`, PTAT). Implementations are typically continuous-time, using resistors for current generation and voltage scaling, and can be based on BJTs or subthreshold MOSFETs. They consist of a core PTAT current generator, a startup circuit, and a feedback mechanism—either an **explicit operational amplifier** or a self-contained structure of **interconnected current mirrors and active devices**—to establish the operating point and provide a buffered output. Low-voltage or high-precision implementations often use a **current-summing** architecture, where PTAT and CTAT currents are combined to form a zero-TC current that is then passed through a resistor to generate the output voltage. **Advanced curvature-corrected references** refine this by generating multiple, distinct currents with different temperature characteristics (e.g., a PTAT current, a CTAT current biased by a PTAT source, and another CTAT-like current biased by a constant-current source). These currents are then weighted and summed to cancel not just the first-order but also the higher-order non-linear temperature dependencies of the PN junction voltage, resulting in an exceptionally low TC. Switched-capacitor implementations of bandgap references, which require clock signals, are classified under **Class 14**.
*   **Rule**: The circuit's primary function must be to generate a stable DC voltage at its output port. It is self-contained and does not require an external signal input for its operation. Its key characterization metrics are accuracy, TC, line/load regulation, and PSRR. This distinguishes it from bias generators (Class 9), which are primarily concerned with establishing specific DC operating points (which may even be intentionally temperature-dependent, e.g., CTAT or PTAT) rather than providing a globally stable, temperature-compensated reference voltage, and from clocked references (Class 14).

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

### 8. Variable-Gain Amplifiers (VGA/PGA) and Analog Multipliers
A circuit that amplifies a signal by a gain factor that is actively controlled by an external signal, or a circuit that produces an output proportional to the product of two analog inputs.
*   **Ports**:
    *   **Required**: At least two analog inputs, which can be single-ended or differential. These serve as:
        *   A primary **signal input** (e.g., `Vin` or `Vinp`/`VIN1`, `Vinn`/`VIN2`) and a **gain control input** (e.g., `Vctrl`/`VB1`/`VCONT1`).
        *   Or, for a multiplier, two symmetrical **signal inputs** (e.g., `VinA`, `VinB`, which may themselves be differential pairs like `VinpA`/`VIN1`, `VinnA`/`VIN2` and `VinpB`/`VIN3`, `VinnB`/`VIN4`).
    *   **Required**: One signal output (e.g., `Vout`/`VOUT1` or `Iout`/`IOUT1`), which can be single-ended or differential. The output can be a voltage or a current.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply an AC signal to the primary signal input. Apply either a DC voltage/current sweep, a sequence of digital codes, or a second AC signal to the control/second input.
    *   **Measurements**:
        *   **Gain Control Characterization**: Perform an AC analysis at each step of the control signal (swept voltage/current or stepped codes) to plot the amplifier's gain vs. the control value. For digital PGAs, this is used to measure gain step size and gain error.
        *   **Bandwidth**: Measure the -3dB frequency at various gain settings (e.g., min, mid, max gain).
        *   **Linearity (IIP3, P1dB)** and **Noise Figure (NF)**: Characterize at various gain settings. For analog multipliers, linearity is a key metric and is often measured using a two-tone test with signals applied to both inputs.
*   **Topologies**:
    *   Common topologies for **analog multipliers** include the **Gilbert Cell** (a four-quadrant multiplier using a stacked structure of a transconductance stage driving a switching quad, often implemented in BJT, CMOS, or BiCMOS) and **parallel-quad CMOS multipliers**. This latter topology leverages the square-law characteristic of MOS transistors by using multiple parallel transistor pairs driven by the input voltages; their output currents are then combined (e.g., summed and differenced via an active current mirror load) to produce an output proportional to the product of the inputs. Depending on the amplitude of its two inputs, a multiplier can operate as a linear analog multiplier (small signals), a balanced modulator/mixer (one large, one small signal), or a phase detector (two large signals). Linearity can be extended using techniques like **emitter degeneration** or **predistortion**.
    *   Common topologies for **analog-controlled VGAs** include varying the **tail current** of a differential pair, altering the load impedance, or adjusting the degeneration network. Single-ended topologies, such as a multi-stage **inverter-based (common-source) amplifier**, are also common. In these, a frequent technique involves using a transistor as a voltage-controlled resistor to implement **variable source degeneration**, **variable source coupling** between input transistors, or to provide **variable shunt feedback** around a gain stage. Alternatively, control voltages can modulate bias currents to change the transconductance and output resistance of the main or source-degenerating transistors. Another technique uses parallel differential pairs where one acts as a variable current shunt.
    *   Topologies for **digitally-controlled PGAs** include **differential pairs with programmable source degeneration networks**, where digitally-controlled switches add or remove resistive branches to change the gain.
    *   This class also covers circuits whose primary controlled parameter is propagation delay, such as **Voltage-Controlled Delay Cells (VCDCs)** used in ring oscillators.
*   **Rule**: The circuit's primary function must be to modulate the amplitude of a signal path via a control input (VGA/PGA), or to explicitly multiply two analog input signals (analog multiplier). This distinguishes it from fixed-gain amplifiers (which lack a gain control input) and from mixers (Class 3), where the primary function is frequency translation using a large-signal, periodic LO signal as one of the inputs.

### 9. Current Mirror Bias Generators / Reference Legs
A circuit that generates one or more stable DC bias voltages, often for biasing the gates of other transistors (e.g., in a current mirror or cascode amplifier). This class includes both simple diode-connected reference legs and more complex self-biasing circuits.
*   **Ports**:
    *   **Required**: One or more DC bias voltage output ports (e.g., `Vbias_main`/`IOUT1`, `Vbias_cascode`/`VB1`/`VB2`).
    *   **Optional**: A reference current input port (`Iref`/`IB1`).
    *   **Optional**: A reference voltage input port (`Vref`) that sets the level of the output voltage.
*   **Stimuli/Measurements**:
    *   **If `Iref` or `Vref` port is present**: Apply DC sources. Perform DC sweeps of these inputs to plot the generated output bias voltages.
    *   **If no external reference (self-biasing)**: Perform a DC sweep of the supply voltage (`VDD`) to measure the line regulation of the output bias voltages.
    *   **Common Measurements**:
        *   DC analysis to find nominal output voltages.
        *   AC analysis to measure the output impedance at each bias voltage port (a key metric for buffer topologies).
        *   DC sweep of temperature to measure a temperature coefficient (TC) of the output voltages.
        *   Transient analysis to ensure the circuit does not have a stable zero-current state and starts up correctly (especially for self-biasing topologies).
*   **Topologies**: Includes simple diode-connected reference legs (used to bias current mirrors), **series stacks of diode-connected transistors and resistors**, and low-impedance buffers like the **Flipped Voltage Follower (FVF)**. More complex generators often take an external reference current and use a network of **current mirrors (simple, cascode, etc.)** and **buffering stages (e.g., source/emitter followers)** to generate multiple, distinct bias voltages for different parts of a main amplifier (e.g., for main current sources, cascode devices, and active loads). This includes specialized sub-circuits like the **high-swing cascode bias generator** (often using a diode-connected device stacked with another transistor) designed to maximize the voltage swing of the amplifier being biased. This class also covers more advanced **self-biasing circuits** that use a resistor to generate a reference current, and can grow into complex, multi-stage systems. A large-scale bias generator, for instance, might combine an internal self-biasing core (which may even use BJT-based sensing for temperature stability, similar to a bandgap core) with additional externally-controlled stages to produce a comprehensive suite of multiple, distinct bias voltage outputs. This includes circuits that generate voltages with specific temperature coefficients, such as the **Proportional to Absolute Temperature (PTAT)** and **Complementary to Absolute Temperature (CTAT)** voltage generators found in bandgap reference cores. These circuits, often self-biasing and using BJTs for temperature sensing, produce intermediate voltages that can be used directly for biasing or combined later to form a temperature-independent reference. A common topology for high-precision biasing involves using a **differential amplifier in a negative feedback loop**. This amplifier compares a divided-down or derived voltage against a reference (either internally generated or from a diode-connected transistor) and drives the gate of a bias transistor to enforce this condition, thereby creating a stable reference current from which multiple bias voltages are derived. Prominent examples include **constant-transconductance (constant-Gm)** bias circuits. Such complex circuits may require a separate start-up circuit to avoid a stable zero-current state.
*   **Rule**: The circuit's primary function must be to produce one or more DC bias voltages as its outputs. It does not produce a mirrored current output. It may be self-biasing (e.g., using an internal resistor as a reference) or may take an external reference current and/or voltage to operate. This distinguishes it from a complete current mirror (Class 12) and a general-purpose DC voltage reference (Class 6). A Class 6 reference is specifically designed for high stability (e.g., low temperature coefficient), whereas a Class 9 bias generator's primary role is to set operating points, and its output may not be fully compensated against process, voltage, or temperature variations.

### 10. Negative Impedance Converters / Oscillator Cores
Active circuits, often with an amplifier-like topology, designed to present a negative resistance or impedance at one of their ports. They are not complete oscillators but serve as the active core that provides the energy to sustain oscillation when connected to a resonant tank (e.g., an an LC circuit).
*   **Ports**:
    *   **Required**: At least one signal input port (e.g., `Vin`/`VIN1`) and one signal output port (e.g., `Vout`/`VOUT1`). The negative impedance is measured at one of these ports (usually the output).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a test AC voltage or current source at the port of interest (e.g., the output) while properly terminating the other port (e.g., grounding the input).
    *   **Measurements**:
        *   **Output Impedance**: AC analysis to plot the real and imaginary parts of the impedance versus frequency. The key metric is verifying a negative real part over the desired frequency range.
        *   **Stability Analysis**: Use stability analysis tools (e.g., `stb` in Spectre) to check for potential oscillation by calculating loop gain.
        *   **Oscillation Verification**: Transient analysis with a connected resonant tank (e.g., an LC load) to verify oscillation startup, frequency, and amplitude.
*   **Rule**: The circuit must be an active two-port network whose primary design purpose is to generate a negative impedance at one of its ports, typically to overcome losses in a resonator and create an oscillator. This is determined by its topology (e.g., specific feedback arrangements like the one provided) and characterization, which focuses on impedance rather than stable linear voltage gain (distinguishing it from Class 1).

### 11. Transconductance Amplifiers (OTA)
An amplifier that converts an input voltage signal into a proportional output current signal.
*   **Ports**:
    *   **Required**: At least one signal voltage input (e.g., `Vin`/`VIN1`, or a differential pair `Vinp`/`Vinn`) and at least one signal current output (`Iout`/`IOUT1`, or a differential pair `Ioutp`/`Ioutn`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply an AC voltage source to the input(s). The output port(s) are typically connected to a load or biased at a suitable DC voltage to allow current measurement.
    *   **Measurements**:
        *   AC analysis to measure transconductance gain (`Gm = Iout / Vin`), -3dB bandwidth, and input/output impedance.
        *   DC sweep of the input voltage to characterize the output current's linear range.
        *   Transient analysis with an input voltage step to measure the slew rate of the output current and settling time.
        *   Noise analysis to measure input-referred voltage noise density.
*   **Topologies**: Topologies range from simple single-ended stages to complex differential designs. Single-ended examples include a basic **common-source/emitter** transistor, the **single-ended cascode** for higher output impedance, and multi-transistor configurations like the **Common-Collector-Common-Emitter (CC-CE) cascade (Darlington pair)** for high input impedance. High-performance differential structures include the simple **differential pair** (MOSFET or BJT, including **Darlington pair** configurations) and more advanced linearized structures like the **cross-coupled quad / Gilbert Quad**, which use active devices to achieve a wider linear input range. These are the classic input stages that convert the differential input voltage into a differential current at the high-impedance collector/drain nodes. Other common differential topologies include the **telescopic cascode** and the **folded cascode**, where the output is taken as a current from a high-impedance node. **BiCMOS implementations** are also common, for example, using a **source-degenerated MOSFET differential pair** for high input impedance, which in turn drives **BJT current mirror loads** to leverage the high transconductance and matching of bipolar devices. This class also includes more complex linearized transconductors that use techniques such as source degeneration, local feedback, or **parallel input stages**. A prominent example of this is the **rail-to-rail input stage**, which uses two complementary differential pairs (e.g., an NMOS pair and a PMOS pair) operating in parallel. The individual pairs may be presented with separate inputs and outputs, but are typically intended to have their inputs tied together and their output currents summed into a common load to achieve a nearly constant transconductance (constant-Gm) over a very wide input common-mode range. More advanced OTAs may employ **dynamic biasing schemes**, where the tail current of the input differential pair is actively boosted in response to a large input signal. This allows the amplifier to achieve a high slew rate and drive large transient currents (e.g., for switched-capacitor loads) while maintaining very low quiescent power consumption, a technique particularly useful in micropower designs operating in the subthreshold region. These are the fundamental building blocks of operational amplifiers but are classified here when used as standalone V-to-I converters. High-performance or fully differential designs often incorporate a Common-Mode Feedback (CMFB) circuit to set the output DC operating point. Some OTA designs may provide one or more **auxiliary current outputs** for purposes such as common-mode sensing or level-shifting, separate from the main signal output(s).
*   **Rule**: The circuit's primary function must be to convert a voltage signal at its input to a a current signal at its output. This distinguishes it from voltage amplifiers (Classes 1 and 7 for continuous-time, and Class 16 for sampled V-to-V) and transimpedance amplifiers (Class 8, I-to-V).

### 12. Current Amplifiers and Current Mirrors
A circuit that converts an input current signal into a related output current signal, which can be a linearly scaled copy (current mirror) or a non-linear function of the input.
*   **Ports**:
    *   **Required**: One or more signal current inputs (e.g., `Iin`/`IIN1`/`IB1`).
    *   **Required**: One or more signal current outputs (e.g., `Iout`/`IOUT1`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply an AC current source superimposed on a DC bias current to the input(s). For differential amplifiers, apply both differential-mode and common-mode AC currents to the inputs.
    *   **Measurements**:
        *   **DC Transfer Characteristics**: Sweep the input DC current and measure the output DC current to find the current transfer ratio (`Iout/Iin`). Sweep the output voltage (while holding input current constant) to determine the output compliance range (the voltage range where `Iout` is stable).
        *   **AC Analysis**: Measure small-signal current gain (`Ai = i_out / i_in`). For differential amplifiers, measure both differential current gain (`Aid = i_out / (i_in_p - i_in_n)`) and common-mode current gain (`Acm = i_out / i_in_cm`) to calculate the Current-Mode Rejection Ratio (CMRR).
        *   **Input/Output Impedance**: Measure input impedance (`Zin`) and output impedance (`Zout`). An ideal current amplifier has a low input impedance (for mirrors, `~1/gm` of the input device) and a high output impedance (for mirrors, `~rds` of the output device).
        *   **Transient Analysis**: Apply an input current step to measure slew rate and settling time of the output current.
*   **Topologies**: Includes fundamental current mirror topologies such as **simple, cascode, Wilson, and wide-swing cascode (NMOS, PMOS, or BJT)**, and specialized low-voltage topologies designed for minimal voltage headroom. These include the **bulk-driven current mirror** (which can be implemented in single-stage or cascode configurations) and the **level-shifted current mirror**, which uses a device like a forward-biased BJT to drop the voltage between the drain and gate of the input transistor, thus reducing the minimum required input compliance voltage. This class also covers enhanced mirror designs that use techniques like **source/emitter degeneration** to improve output resistance and matching, and **beta-helper** circuits (e.g., an emitter follower) to reduce errors caused by finite base/gate current. More complex topologies include **multi-stage or cascaded current mirror networks** that distribute a single reference current to multiple output branches, potentially using a mix of NMOS and PMOS stages. Other topologies include Common-Gate (CG) input stages, current conveyors, and various feedback configurations, such as the use of an active shunt-shunt feedback loop to drastically lower the input impedance (as found in **regulated cascode** or **gain-boosted** current amplifiers). Also included are non-linear current amplifiers, such as those used for log-domain signal processing, where a feedback resistor between the base and collector of a BJT can create an output current that is an exponential function of the input current. This class also includes **differential current amplifiers**, which produce an output current proportional to the difference between two input currents. These can be implemented using **cross-coupled transistors** or other current-subtraction techniques. A prominent example uses two **common-gate** transistors to sense the input currents, with a **current mirror active load** performing the current subtraction to create a single-ended output.
*   **Rule**: The circuit's primary function must be to convert a current signal at its input to a current signal at its output. This is typically identified by a low-impedance current-sensing input port and a high-impedance current-sourcing/sinking output port. This distinguishes it from voltage amplifiers (V-to-V), TIAs (I-to-V), and OTAs (V-to-I). It is also distinguished from complete reference current generators (Class 36), which are self-contained systems that may generate their reference internally, whereas circuits in this class are the core mirroring/amplifying blocks that typically require an external reference current.

### 13. Common-Mode Feedback (CMFB) Circuits
A circuit that senses the common-mode level of a differential input signal and produces a control signal to regulate it, often as part of a larger amplifier.
*   **Ports**:
    *   **Required**: A pair of differential voltage inputs to be sensed (e.g., `Vinp`/`VIN1`, `Vinn`/`VIN2`).
    *   **Required**: An output port that provides a control signal (e.g., `Vcm_ctrl`/`VOUT1`, `IOUT1`, `IOUT2`).
    *   **Optional**: A reference voltage input (`Vcm_ref`/`VREF1`) that sets the target common-mode level. If not present, the target is often set internally.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a DC common-mode voltage to the inputs, sweeping it across the expected operating range (i.e., `Vinp = Vinn = Vcm_sweep`). The differential input is held at zero.
    *   **Measurements**:
        *   **DC Transfer Curve**: Plot the output control signal versus the input common-mode voltage. This characterizes the sensing gain and the valid input common-mode range for the CMFB circuit itself.
        *   **Loop Stability (in context)**: For full characterization, the CMFB circuit is simulated within the main amplifier. Stability analysis (e.g., `stb` in Spectre) is run on the CMFB loop to measure its loop gain, phase margin, and bandwidth.
        *   **Settling Time (in context)**: In a transient simulation with the full amplifier, apply a disturbance that shifts the output common-mode level (e.g., a current pulse injected into an output node) and measure the time it takes for the CMFB loop to restore the correct level.
*   **Topologies**: Includes **continuous-time** CMFB circuits. These can be simple **sensing networks** that produce an output proportional to the common-mode level, or complete **error amplifiers**. Common sensing topologies include **resistive or capacitive averaging networks**. Another widely used approach uses **two interconnected differential pairs** to sense the common-mode voltage while rejecting the differential-mode signal. A third continuous-time topology uses a combination of **source followers and cross-coupled current mirrors** to sum currents that are proportional to the input voltages, thereby sensing the common-mode level. The sensed level (or current) is then often compared against a reference by an error amplifier (which may be a simple current mirror or a dedicated differential pair) to generate the final control output. This class also includes **discrete-time (switched-capacitor)** CMFB circuits that use capacitors and switches to sample the output common-mode level during one clock phase and apply a correction in another.
*   **Rule**: The circuit must have a differential voltage input pair and produce an output (voltage or current) that is a function of the *common-mode level* of the inputs, not their difference. Its primary purpose is to be used in a negative feedback loop to stabilize the DC operating point of a fully differential amplifier.

### 14. Switched-Capacitor (SC) Biasing Circuits and References
Generates a stable DC bias current or voltage whose value is set by capacitors and a clock frequency, making it largely independent of supply voltage, temperature, and process parameters.
*   **Ports**:
    *   **Required**: One or more clock inputs (e.g., `VCLK1`, `VCLK2`).
    *   **Required**: One or more DC bias outputs, which can be a mirrored current (`Iout`) or a bias voltage (`Vbias`/`VREF1`).
    *   **Optional**: One or more bias current inputs (e.g. `IB1`, `IB2`) for circuits like bandgap references.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Requires one or more periodic clock signals, often with non-overlapping phases.
    *   **Measurements**:
        *   DC operating point analysis (with clocks running in a PSS simulation) to find the nominal output current/voltage.
        *   DC sweep of the supply voltage (`VDD`) and clock frequency (`f_clk`) to measure line regulation and frequency dependence.
        *   DC sweep of temperature to measure the temperature coefficient (TC).
        *   Transient analysis with VDD ramping up to ensure proper start-up (these circuits often have a zero-current stable state and may require a dedicated startup circuit).
        *   Measure the transconductance (`gm`) of a designated transistor to verify the "constant-Gm" property.
*   **Topologies**: This class includes high-precision **switched-capacitor bandgap references**. In these circuits, a switched-capacitor network replaces traditional resistors for sampling BJT voltages and performing weighted summation. This approach offers precise voltage scaling based on capacitor ratios and often incorporates **Correlated Double Sampling (CDS)** to cancel the DC offset and low-frequency 1/f noise of the internal operational amplifier, leading to very high accuracy.
*   **Rule**: The circuit must generate a DC bias current or voltage and *must* require one or more clock inputs for its core operation, typically using a switched-capacitor network as a reference element. This distinguishes it from DC-only references (Class 6) and bias generators (Class 9).

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

### 16. Switched-Capacitor (SC) / Switched-Resistor (SR) Amplifiers & Integrators
A discrete-time amplifier or integrator whose operation is defined by distinct phases controlled by one or more clock signals.
*   **Ports**:
    *   **Required**: At least one analog signal input (e.g., single-ended `Vin`/`VIN1` or differential `Vinp`/`VIN1`, `Vinn`/`VIN2`), at least one analog signal output (`Vout` or `Voutp`/`VOUT1`, `Voutn`/`VOUT2`), and one or more clock inputs (`Vclk`/`VCLK1`, `VCLK2`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: An analog waveform (e.g., DC step or sine wave) at the input and one or more periodic, often non-overlapping, digital clock signals.
    *   **Measurements**:
        *   **Gain Accuracy**: Measured in transient analysis by applying a known DC input and measuring the settled DC output at the end of the amplification phase.
        *   **Settling Time**: The time required for the output to settle to within a specified error band of its final value during the amplification phase.
        *   **Charge Injection, Clock Feedthrough & Residual Offset**: Measured as the offset error at the output, typically with the inputs grounded.
        *   **Frequency Response**: Characterized using PSS/PAC analysis to get the discrete-time transfer function.
*   **Topologies**: Topologies are based on a high-gain operational amplifier configured with a network of switches, capacitors, and sometimes resistors. The operation is controlled by a clocking scheme, typically with two non-overlapping phases (a sampling phase and a charge-transfer phase), but more complex multi-phase schemes are also used. During these phases, switches reconfigure the connections to sample input voltages onto capacitors and then transfer that charge to a feedback capacitor to generate the output. Common configurations include classic **inverting and non-inverting SC amplifiers** where gain is set by capacitor ratios, and **SC integrators/filters** (including **summing integrators** and the classic **lossy integrator** which forms a first-order low-pass filter). Other techniques include **switched-resistor (SR) integrators** and **auto-zeroing** or **Correlated Double Sampling (CDS)** amplifiers that cancel their own DC offset and 1/f noise. The core amplifier is typically a high-gain design (e.g., a **folded-cascode or telescopic cascode OTA**) to ensure gain accuracy and can be single-ended or a high-performance, fully differential design (e.g., a **two-stage amplifier** with a folded-cascode first stage and CMFB). A common application is a **discrete-time pre-amplifier**, often used in a cascade for high-speed comparators or ADCs. Such a pre-amplifier may operate in multiple clock phases, including an **autozero phase** (where switches place the amplifier in a feedback configuration to sample its own offset) and a **reset phase** (where switches short the outputs to establish a common starting voltage), before entering the main **amplification phase**. The core amplifier for these high-speed applications is often a wide-bandwidth design, such as a **cascode OTA with clamped active loads** to limit voltage swing and improve recovery time. These amplifiers can be implemented in CMOS or **BiCMOS**, with some BiCMOS designs leveraging a powerful **Class AB BJT push-pull output stage** to achieve high current drive capability for rapidly charging load capacitors. This class also includes more integrated "dynamic" or "switched" operational amplifiers where the conventional continuous-time input stage (e.g., a differential pair) is entirely replaced by a switched-capacitor network that directly drives a high-gain output stage. In these designs, the capacitors and switches perform both offset cancellation and input signal sampling in one phase, and then drive the output stage during a subsequent amplification phase.
*   **Rule**: The circuit's primary function must be to perform voltage amplification or integration using a network of switches, capacitors, and/or resistors, requiring at least one clock signal for its operation. The output is a discrete-time signal, valid at the end of a clock phase. This distinguishes it from continuous-time amplifiers (Classes 1 and 7) and simple unity-gain sample-and-hold circuits (Class 5).

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

### 18. ESD Protection Circuits
Passive networks designed to protect sensitive internal circuitry from high-voltage electrostatic discharge events by clamping voltages and shunting high currents.
*   **Ports**:
    *   **Required**: An external port to be protected (`PIN`/`VIN1`) and an internal protected port (`POUT`/`VOUT1`). The circuit is connected between these two ports and referenced to the supply rails (`VDD`, `VSS`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: High-current pulses emulating ESD events, typically using Transmission Line Pulsing (TLP) to generate an I-V curve. Standard ESD models like the Human Body Model (HBM) can be used for transient verification.
    *   **Measurements**:
        *   **I-V Clamping Curve (TLP)**: Plot the clamping voltage at the protected node (`POUT`) versus the injected ESD current at the external port (`PIN`).
        *   **Failure Current (`It2`)**: The peak current the device can withstand before permanent damage, determined from the TLP curve.
        *   **Transient Clamping Voltage**: The peak voltage reached at the protected node during a specific ESD event (e.g., HBM pulse).
        *   **Impact on Signal Integrity**: S-parameter analysis (`S21`, `S11`) to measure insertion loss and return loss during normal, small-signal operation.
*   **Rule**: The circuit must be a passive or semi-passive network (typically diodes, resistors, SCRs, or GG-NMOS) with an input and output. Its primary function is to provide a low-impedance path to the supply rails when the input voltage exceeds the normal operating range, and it is characterized by its response to high-voltage/high-current stress tests. This distinguishes it from a passive filter (Class 11), which is characterized by its linear frequency response.

### 19. Analog Adder / Subtractor / Combiner
An active circuit that combines (adds or subtracts) two or more input signals to produce a single output signal. This includes both baseband summing amplifiers and RF power combiners.
*   **Ports**:
    *   **Required**: At least two distinct signal inputs (e.g., `VinA`, `VinB`). These can be single-ended (e.g., `VIN1`, `VIN2`) or differential pairs.
    *   **Required**: One or more signal outputs (`Vout`), which can be single-ended (e.g., `VOUT1`, `VOUT2`) or differential. If multiple outputs are present, they typically carry the same combined signal.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply distinct AC signals to each input port. For RF combiners, these are typically high-frequency tones with a specific phase relationship.
    *   **Measurements**:
        *   **Transfer Function**: Perform AC or S-parameter analysis from each input to the output to verify the gain and bandwidth for each path.
        *   **Linearity (IMD)**: For baseband adders, apply multiple tones and measure intermodulation distortion.
        *   **Combining Efficiency/Power**: For RF power combiners, perform Harmonic Balance analysis to measure output power and efficiency as a function of the input signals' phase difference.
        *   **Transient Verification**: Apply signals to all inputs simultaneously and observe the output waveform to verify the combination.
*   **Topologies**: Includes op-amp based summing amplifiers and **transconductance-based summing amplifiers**, where multiple parallel input transconductors (e.g., common-source stages) have their output currents summed at a common node, which is then converted back to a voltage by a load or a subsequent gain stage. This class also includes **RF Power Combiners**, such as the output stage of an **outphasing (LINC) amplifier**, where two parallel, non-linear amplifier stages are current-summed at a common output node to reconstruct a linear, amplitude-modulated signal.
*   **Rule**: The circuit must have at least two distinct signal input ports and one signal output port. Its primary function must be to produce an output signal that is a combination (sum or difference) of the input signals. This distinguishes it from a standard amplifier (Classes 1, 7, or 16) which has only one primary signal input, and from a mixer (Class 3) which performs non-linear multiplication for frequency conversion.

### 20. Differential & Mixed-Mode RF Amplifiers (LNA, PA, Baluns)
An RF amplifier that possesses **at least one** differential signal port. This class encompasses Fully Differential Amplifiers (DIDO), Active Baluns (Single-to-Diff), and Differential Combiners (Diff-to-Single) operating in the RF domain.
* **Ports**:
    * **Required**: At least one **Differential Signal Port** pair (Input or Output).
    * **Configurations**:
        * **DIDO (Diff-In / Diff-Out)**: `RFinp`/`RFinn` $\to$ `RFoutp`/`RFoutn`.
        * **SIDO (Single-In / Diff-Out)**: Single-Ended Input $\to$ Differential Output (Active Balun).
        * **DISO (Diff-In / Single-Out)**: Differential Input $\to$ Single-Ended Output.
* **Stimuli/Measurements**:
    * **Stimuli**: Use standard Ports for single-ended terminals and Balanced Ports (or dual ports with $180^\circ$ phase shift) for differential terminals.
    * **Measurements**:
        * **Mixed-Mode S-Parameters**: This is the defining measurement set.
            * **Differential Gain ($S_{dd21}$)**: For DIDO.
            * **Single-to-Differential Gain ($S_{sd21}$)**: For Active Baluns.
            * **Common-Mode Rejection**: ($S_{cc21}$ and conversion parameters like $S_{cd21}$).
        * **Noise Figure (NF)**: Differential Noise Figure.
        * **Linearity**: IIP3/P1dB using two-tone tests (handling differential drive levels).
        * **Balance/Phase Error**: Deviation from ideal $180^\circ$ phase shift between differential output nodes.
* **Topologies**:
    * **Fully Differential**:  Standard differential pairs with inductive degeneration or cross-coupled capacitors (capacitive cross-coupling) for $g_m$-boosting.
    * **Active Baluns (S-to-D)**: **Noise-Canceling LNAs** (combining a Common-Gate path and a Common-Source path to produce balanced outputs), or differential pairs driven single-endedly (common gate node grounded).
    * **Differential PAs**: Push-pull configurations or transformer-coupled output stages.
* **Rule**: The circuit is an RF Amplifier that has **at least one differential signal port pair**.
    * **Priority:** If a circuit has a single-ended input but a differential output, it belongs here (Class 20), not Class 38.
    * **Distinction:** Distinguished from Class 7 (Baseband Diff Amps) by the presence of RF matching components (Inductors, Transmission Lines) and characterization via S-parameters.

### 22. Voltage-Controlled Variable Capacitors (Varactors)
A circuit that provides a voltage-tunable capacitance, typically used for frequency tuning in oscillators or filters.
*   **Ports**:
    *   **Required**: Two terminals across which the variable capacitance is presented (e.g., `Port1`/`IB1`, `Port2`/`VCONT1`).
    *   **Required**: An analog control voltage input (e.g., `Vctrl`). This control input may be one of the capacitor terminals (e.g., `Vctrl` is the same node as `Port2`).
    *   **Optional**: A bias current port (`Ibias`) may be required if the varactor includes an active biasing scheme. This bias port may be the same node as one of the capacitor terminals (e.g., `Ibias` is sourced into `Port1`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Sweep the DC control voltage (`Vctrl`) over its operating range. For circuits requiring a bias current, provide a constant DC current source.
    *   **Measurements**:
        *   **C-V Curve**: At each step of the control voltage sweep, perform an AC analysis (or S-parameter analysis) to extract the capacitance between the capacitor terminals. Plot the capacitance versus the control voltage.
        *   **Quality Factor (Q)**: From the same AC/SP analysis, calculate the quality factor (`Q = imag(Y)/real(Y)`) of the varactor across frequency and as a function of the control voltage.
*   **Topologies**: Includes single or parallel **MOS varactors** (often accumulation-mode for monotonic C-V curves) and reverse-biased PN junction diodes. May include an integrated active biasing network (e.g., diode-connected transistors) to set the DC operating point of the capacitor terminals.
*   **Rule**: The circuit's primary function must be to act as a capacitor whose value is controlled by a separate analog voltage input. It must have at least three terminals: two for the capacitance and one for the control voltage. This distinguishes it from fixed two-terminal passive impedance networks (Class 34).

### 23. Charge Pump
A circuit that converts digital "Up" and "Down" control pulses into a current that is sourced or sunk from an output node. It is typically used with an external or integrated loop filter to generate an analog control voltage.
*   **Ports**:
    *   **Required**: Two digital control inputs, one for "Up" (e.g., `LOGICQA1`/`UP`/`VCONT2`) and one for "Down" (e.g., `LOGICQB1`/`DN`/`VCONT4`).
    *   **Required**: One analog output port (e.g., `Iout`/`net20`) from which current is sourced/sunk. If a loop filter is integrated, this port provides the output voltage.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply periodic, digital pulse trains to the `UP` and `DN` inputs. If the circuit is a standalone charge pump, an external load (typically a capacitor representing the loop filter) must be connected to the output for transient analysis.
    *   **Measurements**:
        *   **Current Matching**: Apply long, separate pulses to the `UP` and `DN` inputs and measure the output current directly (in DC analysis) or the output voltage slew rate (`dV/dt`) across the load capacitor (in transient analysis) to verify that the sourced and sinked currents are equal.
        *   **Output Ripple**: Apply simultaneous, narrow, and identical pulses to both inputs (simulating a locked PFD state) and measure the peak-to-peak voltage variation on the output node (with load capacitor).
        *   **Voltage Compliance Range**: Sweep the DC voltage of the output node and measure the output current to determine the voltage range over which the charge pump currents remain matched and within specification.
*   **Rule**: The circuit must have two digital inputs corresponding to "Up" and "Down" commands and a single analog output that sources or sinks current based on these commands. This class covers both standalone charge pumps and those with an integrated loop filter. It is distinguished from complete PLL blocks (Class 17), which take reference and feedback clocks directly rather than discrete Up/Down pulses.

### 24. Digital Combinatorial Logic Gates
Digital circuits that perform a stateless, combinatorial logic function (e.g., AND, NAND, OR, XOR) on two or more input signals. This class covers high-speed logic families like Current-Mode Logic (CML).
*   **Ports**:
    *   **Required**: Two or more digital signal inputs, which can be single-ended or differential (e.g., `LOGICA1`/`LOGICA2`, `LOGICB1`/`LOGICB2`).
    *   **Required**: One or more digital signal outputs, which can be single-ended or differential (e.g., `VOUT1`, `VOUT2`).
    *   **Optional**: A tail current bias port (e.g., `IB1`) for current-steering logic families like CML.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply digital waveforms (pulses, clocks) to the inputs to cover the gate's truth table.
    *   **Measurements**:
        *   **Transient analysis** is the primary simulation.
        *   **Logical Function Verification**: Verify that the output corresponds to the correct logical combination of the inputs for all states.
        *   **Propagation Delay**: Measure the time from an input transition to the corresponding output transition (e.g., `t_pLH`, `t_pHL`).
        *   **Rise/Fall Times**: Measure the 10%-90% or 20%-80% transition times of the output signals.
        *   **Power Consumption**: Measure static and dynamic power consumption.
*   **Topologies**: Includes various digital logic families. Common implementations are based on **static CMOS logic** (using complementary pull-up PMOS and pull-down NMOS networks), **pass-gate logic** (using NMOS, PMOS, or transmission gates to steer signals, commonly used in clock multiplexers), or high-speed current-steering families like **Current-Mode Logic (CML)**. The functions implemented range from basic gates like **AND, NAND, OR, NOR, XOR** to more complex combinatorial blocks such as **multiplexers (MUX)** and decoders.
*   **Rule**: The circuit must implement a stateless, combinatorial logic function with at least two distinct logic inputs (e.g., A and B) and at least one logic output. This distinguishes it from clock buffers/inverters (Class 15), which typically have a single signal input path, and sequential logic like latches/flip-flops (Class 25).

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

### 26. Regenerative Frequency Dividers
Analog/RF circuits that perform frequency division by locking to a sub-harmonic of an input signal, typically using a mixer and filter in a feedback loop.
*   **Ports**:
    *   **Required**: One high-frequency clock input, which can be single-ended or differential (e.g., `CLK_IN`/`VIN1`, `VIN2`).
    *   **Required**: One frequency-divided clock output, which can be single-ended or differential (e.g., `CLK_OUT`/`VOUT1`, `VOUT2`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a high-frequency sinusoidal or square-wave clock to the input.
    *   **Measurements**:
        *   **Operating Frequency Range (Lock Range)**: Sweep the input clock frequency and check the output for correct and stable division. This determines the range over which the divider operates.
        *   **Functionality Verification**: Perform a transient analysis to confirm the output frequency is `f_in / N` (e.g., `f_in / 2`).
        *   **Phase Noise**: PSS/PNOISE analysis to measure the phase noise of the output clock relative to the input.
        *   **Power Consumption**.
*   **Topologies**: Includes **Miller dividers**, which use a mixer (active or passive) and a filter in a regenerative feedback loop. Also includes **Injection-Locked Oscillators (ILOs)**, where a free-running oscillator is injected with a signal at a multiple of its oscillation frequency, forcing it to lock.
*   **Rule**: The circuit must perform frequency division using an analog regenerative mechanism (mixing/feedback or injection locking). This distinguishes it from digital logic-based dividers (Class 25), which use clocked latches or flip-flops to achieve division.

### 27. Digital-to-Analog Converters (DAC)
A circuit that converts a multi-bit digital input word into a proportional analog output signal (current or voltage).
*   **Ports**:
    *   **Required**: Multiple digital input ports representing the input code (e.g., `D0`, `D1`, ... or `VCONT1`, `VCONT2`, `VCONT3`).
    *   **Required**: One analog output port, which can be a current (`Iout`/`IOUT1`) or a voltage (`Vout`).
    *   **Optional**: A reference input, which can be a current (`Iref`/`IREF1`) for scaling a current-steering DAC, or a voltage (`Vref`) for resistor-string or switched-capacitor DACs.
    *   **Optional**: A clock input (`CLK`) for latched or pipelined DACs.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a sequence of digital codes to the inputs, typically ramping from all '0's to all '1's.
    *   **Measurements**:
        *   **Static Linearity (DC Analysis)**: Perform a DC analysis at each input code and measure the corresponding analog output.
        *   **Differential Non-Linerity (DNL)**: The deviation in step size between adjacent codes from the ideal step size (LSB).
        *   **Integral Non-Linerity (INL)**: The maximum deviation of the actual transfer curve from an ideal straight line.
        *   **Gain Error & Offset Error**: Deviations in the slope and y-intercept of the best-fit line through the transfer curve.
        *   **Dynamic Performance (for high-speed DACs)**:
            *   **Settling Time**: Time for the output to settle to within a certain error band after a code transition.
            *   **Spurious-Free Dynamic Range (SFDR)**: Measured by applying a digital sine wave to the input and analyzing the output spectrum for the largest spurious tone relative to the fundamental.
*   **Topologies**: Includes **current-steering DACs** (which use an array of switched current sources), R-2R ladders, resistor-string DACs, and charge-redistribution (switched-capacitor) DACs.
*   **Rule**: The circuit must have a multi-bit digital input (two or more control bits) and a single analog output (current or voltage). Its primary function must be to convert the digital code into a proportional analog level. This distinguishes it from simple single-bit current-steering cells (Class 12).

### 28. Switching-Mode RF Power Amplifiers (e.g., Class D, E, F)
An amplifier that uses its active device(s) as switches for high-efficiency RF power amplification, often for constant-envelope signals.
*   **Ports**:
    *   **Required**: One RF signal input, which can be single-ended (`RFin`/`VIN1`) or differential (`RFinp`/`RFinn`). The input is driven by a large-signal waveform (e.g., a square wave or the locking signal for an oscillator).
    *   **Required**: One RF signal output, which can be single-ended (`RFout`/`VOUT1`) or differential (`RFoutp`/`RFoutn`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a large-signal periodic input (e.g., square wave or pulsed sinusoid) at the desired operating frequency. The output must be terminated with the correct load impedance for which the amplifier was designed.
    *   **Measurements**:
        *   **Power Added Efficiency (PAE) and Drain Efficiency (DE)**: This is the primary metric, measured using Harmonic Balance or a long transient simulation.
        *   **Output Power**: The power delivered to the fundamental frequency component at the load.
        *   **Waveform Verification**: Transient analysis to inspect the drain voltage and current waveforms of the switching transistor to verify optimal switching conditions (e.g., Zero Voltage Switching (ZVS) or Zero Current Switching (ZCS)).
        *   **Device Voltage Stress**: The peak voltage across the main switching device, a critical reliability metric.
        *   **Harmonic Content/Suppression**: The power level of harmonics at the output, measured with PSS/Harmonic Balance.
*   **Topologies**: Includes **Class E** amplifiers (which use a specific load network with an RF choke and shunt capacitor to shape waveforms for ZVS and ZVDS), **Class D** amplifiers (which use a pair of switches in a push-pull or bridge configuration), and **Class F** amplifiers (which use resonant networks to shape drain voltage/current into square/half-sine waves). This class also covers **injection-locked power amplifiers (ILPAs)**, where a switching oscillator is locked to an input signal's phase, allowing for high-efficiency amplification of phase-modulated signals.
*   **Rule**: The circuit must be an RF power amplifier where the active device operates as a switch (driven into cutoff and triode regions), not as a linearly controlled current source. The input is a large-signal drive, and the primary characterization focuses on efficiency and output power, rather than small-signal metrics like S-parameters or linearity metrics like IIP3. This distinguishes it from linear/quasi-linear PAs (Classes 1 and 20).

### 29. Voltage Comparators and Schmitt Triggers
A circuit that compares two analog input voltages and produces a digital output indicating which is larger. This class covers both continuous-time comparators (including Schmitt triggers with hysteresis) and clocked/dynamic comparators.
*   **Ports**:
    *   **Required**: At least two analog voltage inputs, one non-inverting (e.g., `Vinp`/`VIN1`) and one inverting (e.g., `Vinn`/`VIN2`). One of these is typically driven by a signal while the other is connected to a reference voltage. This circuit may also have separate dedicated reference inputs (e.g. `VREF1`, `VREF2`).
    *   **Required**: At least one digital logic-level output (e.g., `Vout`/`VOUT1`), which can be single-ended or differential.
    *   **Optional**: A clock input for clocked/dynamic comparators. An enable or latch-enable (`LE`) pin to control the comparison/latching operation.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a DC voltage to one input (the reference) and a slow-ramping voltage (e.g., a triangle wave) that sweeps across the reference level to the other input.
    *   **Measurements**:
        *   **DC Transfer Curve / Hysteresis**: Perform a DC or transient analysis to plot `Vout` vs. `Vin`. Measure the input switching thresholds for rising and falling inputs to determine the hysteresis width.
        *   **Input Offset Voltage**: The differential input voltage required to make the output switch when it is not in the middle of a hysteresis window.
        *   **Propagation Delay**: Perform a transient analysis with a step input (with a defined overdrive voltage) to measure the time from the input crossing the threshold to the output reaching 50% of its final value.
        *   **Power Supply Rejection Ratio (PSRR)**.
*   **Topologies**: Includes open-loop high-gain differential amplifiers, which can be **single-stage** or **multi-stage** designs. A common multi-stage architecture consists of a differential pre-amplifier stage followed by a second gain stage and/or a high-drive **push-pull output stage (such as one or more cascaded CMOS inverters)**. This class also includes **regenerative latch-based comparators**, which can be continuous-time or clocked.
    *   **Continuous-Time (Schmitt Triggers)**: A classic continuous-time regenerative topology consists of a differential input pair driving a composite active load that combines simple loading elements (e.g., a pair of **diode-connected transistors**) with a **cross-coupled regenerative latch**. The design can be single-stage, merging pre-amplification and latching, or multi-stage, with a dedicated pre-amplifier preceding the latch. The relative strength of the latch determines the amount of hysteresis, forming the core of a **Schmitt Trigger**. Another advanced continuous-time topology is the **self-biased or adaptively-biased comparator**, which uses two complementary differential pairs (e.g., NMOS and PMOS) that act as loads for each other.
    *   **Clocked / Dynamic**: These comparators operate in distinct reset and evaluation phases controlled by a clock. They typically use a regenerative latch to achieve high-speed decision making. A common architecture involves a pre-amplification stage followed by a clocked latch. More power-efficient "dynamic" topologies omit a static pre-amplifier and create an initial voltage imbalance directly on the latch nodes during a reset/sampling phase. This imbalance is then amplified to full logic levels by positive feedback during an evaluation/regeneration phase. There are two common ways to establish the initial imbalance: one method pre-charges the latch's output nodes to a common voltage (e.g., VDD), and then an input differential pair is enabled to discharge the nodes at different rates. Alternatively, the input and reference voltages can be directly sampled onto the latch's output nodes via switches during the reset phase. The regenerative latch itself is often a **cross-coupled inverter pair**, which can be implemented with just a PMOS pair, or with both a **cross-coupled PMOS pair** and a **cross-coupled NMOS pair** to provide stronger, faster regeneration. These can be implemented in pure CMOS or in high-speed **BiCMOS** technologies, often using cascaded **emitter-follower buffers** for low-impedance output drive. High-performance clocked comparators may also use **switched-capacitor front-ends** to a sample the input and perform **auto-zeroing** to cancel the comparator's own DC offset and low-frequency noise.
*   **Rule**: The circuit must take at least one analog signal input and produce a binary, digital-level output based on comparing that input to a reference level. This includes circuits with inherent or designed-in hysteresis (Schmitt triggers). Key characterization metrics are propagation delay, offset, and hysteresis, distinguishing it from linear amplifiers (Classes 1, 7, and 16) which are designed for proportional analog output.

### 30. Current Comparators
A circuit that compares two analog input currents and produces a digital output indicating which is larger.
*   **Ports**:
    *   **Required**: At least two analog current inputs, one for the signal (e.g., `Iin`/`IIN1`) and one for the reference (e.g., `Iref`/`IB1`).
    *   **Required**: At least one digital logic-level voltage output (e.g., `Vout`/`VOUT1`).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a constant DC current source to one input (the reference) and a slow-ramping DC current source to the other input that sweeps across the reference level.
    *   **Measurements**:
        *   **DC Transfer Curve / Hysteresis**: Perform a DC or transient analysis to plot the output voltage vs. the input current. Measure the input switching thresholds for rising and falling input currents to determine any hysteresis.
        *   **Input Offset Current**: The differential input current required to make the output switch state.
        *   **Propagation Delay**: Perform a transient analysis with a step in the input current (with a defined overdrive current) to measure the time from the input crossing the reference threshold to the output reaching 50% of its final value.
*   **Rule**: The circuit must take at least one analog current signal input and produce a binary, digital-level voltage output based on comparing that input to a reference current level. This distinguishes it from voltage comparators (Class 29), which have voltage inputs, and from current amplifiers (Class 12), which have a proportional analog current output.

### 31. Timing Circuits (e.g., 555 Timer)
A mixed-signal circuit that generates time delays (monstable mode) or oscillations (astable mode) based on the charging and discharging of an external RC network.
*   **Ports**:
    *   **Required**: At least two analog voltage inputs for timing control: a `Threshold` input (e.g., `VCONT1`) and a `Trigger` input (e.g., `VCONT2`).
    *   **Required**: One digital logic-level output (`Vout`/`VOUT1`).
    *   **Optional**: A `Control Voltage` input (e.g., `VCONT5`) to access or override an internal reference voltage, a `Reset` input to force the output to a known state, and a `Discharge` output (often open-drain) to discharge the external timing capacitor.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Requires connection of an external RC network to the `Threshold`, `Trigger`, and `Discharge` pins to configure for astable (oscillator) or monostable (one-shot) operation.
    *   **Measurements (Transient Analysis)**:
        *   **Astable Mode**: Measure the frequency, period, and duty cycle of the output waveform.
        *   **Monostable Mode**: Apply a trigger pulse to the `Trigger` input and measure the resulting output pulse width.
        *   **Threshold and Trigger Voltage Levels**: Verify the exact input voltage levels that cause the output to switch states.
        *   **Output Voltage Levels (`V_OH`, `V_OL`)** and current drive capability.
*   **Rule**: The circuit must be a stateful block containing voltage comparators, a flip-flop, and an internal voltage reference. Its primary function is to produce time-based digital output signals controlled by analog voltage levels on dedicated 'Threshold' and 'Trigger' inputs, typically in conjunction with an external RC network. This distinguishes it from simple comparators (Class 29, which lack the internal state machine) and free-running oscillators (Class 2, which may not have this specific control structure).

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

### 35. Active Inductors / Gyrators
An active circuit that uses transistors to synthesize a frequency-dependent impedance that emulates an inductor.
*   **Ports**:
    *   **Required**: One or two signal ports across which the inductive impedance is presented. For a one-port implementation, this is a single terminal (e.g., `IN`/`IB1`) referenced to ground.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply an AC test source (voltage or current) to the signal port(s). The circuit must be biased into its active region, typically with a DC current source connected to the signal port.
    *   **Measurements**:
        *   **Impedance vs. Frequency**: AC analysis to plot the real and imaginary parts of the input impedance (`Zin`) versus frequency.
        *   **Equivalent Inductance (`L_eq`)**: Calculated from the imaginary part of the impedance (`imag(Zin) / (2*pi*f)`) in the operating frequency range.
        *   **Quality Factor (Q)**: Calculated from the ratio of the imaginary to the real part of the impedance (`imag(Zin) / real(Zin)`).
*   **Topologies**: Includes **gyrator-based** circuits that use two transconductors in a feedback loop to convert a capacitance into an inductance. A common single-transistor implementation of this principle uses a single active device to realize the gyrator.
*   **Rule**: The circuit must be a one-port or two-port active network whose primary function is to present a positive inductive impedance at its port(s). It is characterized by its Z-parameters, not by gain or other amplifier metrics. This distinguishes it from one-port negative impedance converters (Class 10), which generate a negative resistance, and from passive networks (Class 34).

### 36. Reference Current Generators
A circuit that generates a stable DC output current, often designed to be independent of power supply and temperature variations.
*   **Ports**:
    *   **Required**: One or more DC current outputs (e.g., `Iout`/`IB1`, `IB2`).
    *   **Optional**: A reference voltage input (`Vref`/`VREF1`) or a reference current input (`Iref`) that sets the output current's value. Some topologies are self-referencing and may not have an external reference input.
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a stable DC reference voltage or current if required.
    *   **Measurements**:
        *   **DC Output Current**: The nominal output current at a reference temperature and supply.
        *   **Line Regulation**: DC sweep of the supply voltage (`VDD`) to measure the change in output current (`ΔIout / ΔVdd`).
        *   **Load Regulation / Output Compliance**: DC sweep of the output voltage to find the voltage range over which the output current remains stable (characterizes output impedance).
        *   **Temperature Coefficient (TC)**: DC sweep of temperature to plot the output current and calculate its drift (in ppm/°C).
        *   **Power Supply Rejection Ratio (PSRR)**: AC analysis on the supply rail to measure the rejection of supply noise to the output current.
*   **Topologies**: Topologies can be externally referenced or self-referencing.
    *   **Externally Referenced**: These circuits use a reference voltage (`Vref`) and a resistor (`Rext`) to set a current (`I = Vref / Rext`), often using an **operational amplifier in a negative feedback loop** to enforce the voltage drop across the resistor. The resulting current is then mirrored to the output.
    *   **Self-Referencing**: These circuits use an internal feedback loop to generate a current that is largely dependent on device parameters and resistors. This category also includes simpler configurations like a **basic current mirror where the reference current is set internally by a resistor connected to the supply rail** (`I_ref = (VDD - V_BE) / R`). While less stable against supply variations than more complex designs, their function is still to generate a reference current. More advanced examples, which are often designed to be insensitive to the supply voltage, include the **threshold-referenced MOS current source**, the **Widlar** current source, and the **Peaking current source**. The most common high-performance self-biasing topologies use a feedback loop (often composed of **two interconnected current mirrors**) to generate a current with a well-defined temperature coefficient. A stable, non-zero operating point is created by introducing an asymmetry, typically by comparing two different voltage drops created by components in the source paths of transistors within the loop. This principle is the basis for **PTAT current sources** (based on the voltage difference, `ΔV_BE`, between two BJTs) and **CTAT current sources** (often based on a BJT's `V_BE` or a diode's forward voltage). These self-biased circuits almost always require a **dedicated start-up circuit** to ensure they settle into the desired operating point rather than a stable zero-current state. The core reference current is then typically mirrored to one or more output branches. The output mirror stage often incorporates enhancements like **cascode structures** for higher output impedance, **beta-helpers** to reduce current gain errors in BJT designs, or **emitter/source degeneration** for improved matching and output resistance.
*   **Rule**: The circuit's primary function must be to generate a stable DC current at its output port. It is a typically characterized by its DC accuracy, temperature coefficient, and line/load regulation. This distinguishes it from bias generators that produce voltage outputs (Class 9) and from general-purpose transconductance amplifiers (Class 11) which are designed and characterized for AC signal processing.

### 37. Analog Folding Circuits / Waveshapers
A circuit that performs a non-linear, periodic waveshaping function on an analog input, creating a "folded" transfer characteristic (e.g., sawtooth or triangle wave), typically as a front-end for a folding ADC.
*   **Ports**:
    *   **Required**: One primary analog signal input (e.g., `Vin`/`VIN1`).
    *   **Required**: One or more analog signal outputs (e.g., single-ended `Vout` or differential `Voutp`/`VOUT1`, `Voutn`/`VOUT2`).
    *   **Required**: Multiple distinct DC reference voltage inputs that define the folding points (e.g., `Vref1`/`VIN2`, `Vref2`/`VIN3`, ...).
*   **Stimuli/Measurements**:
    *   **Stimuli**: Apply a slow voltage ramp (e.g., triangle wave) to the signal input that sweeps across the full range defined by the reference voltages. Apply stable DC voltages to the reference inputs.
    *   **Measurements**:
        *   **DC Transfer Curve**: The primary measurement. Plot the output voltage vs. the input voltage to verify the folded (e.g., triangle/sawtooth) characteristic. Key metrics are the locations of the fold points (determined by the reference voltages), the peak/valley voltages, and the linearity of each segment.
        *   **Bandwidth / Frequency Response**: AC analysis to determine the small-signal bandwidth. For high-speed applications, transient analysis with a high-frequency sine wave input is used to check for distortion and verify the "bandwidth multiplication" effect where the output fundamental frequency can be a multiple of the input.
*   **Topologies**: The defining topology consists of multiple parallel transconductor stages (typically **differential pairs**) whose inputs are driven by a common signal and a set of staggered DC reference voltages. The output currents of these stages are summed into a common load (e.g., resistive loads). Some stages are connected non-invertingly while others are cross-coupled (inverting) to the output, causing the slope of the transfer function to change direction at each reference threshold, thereby creating the folding effect.
*   **Rule**: The circuit must have one primary analog signal input, multiple DC reference inputs, and an analog output. Its primary function must be to produce a non-linear, periodic (folded) output transfer curve, characterized by multiple changes in the sign of its slope. This distinguishes it from linear amplifiers (which have a constant slope), comparators (which have a digital output), and simple rectifiers/clippers (Class 32, which typically have only one or two changes in slope and lack multiple reference inputs). 

### 38. Single-Ended RF Low-Noise Amplifiers (SISO LNA)
A fundamental RF gain block with a strict **Single-Input / Single-Output (SISO)** interface. Designed for $50\Omega$ impedance matching, low noise, and power gain.
* **Ports**:
    * **Required**: Exactly **ONE** RF Input Port (Single-ended, e.g., `RFin`/`IN`).
    * **Required**: Exactly **ONE** RF Output Port (Single-ended, e.g., `RFout`/`OUT`).
    * **Exclusion**: If the circuit has `inp`/`inn` or `outp`/`outn`, it is **disqualified** (Move to Class 20).
* **Stimuli/Measurements**:
    * **Stimuli**: S-Parameter Ports ($Z_0 = 50\Omega$) and Harmonic Balance sources.
    * **Measurements**:
        * **S-Parameters ($S_{11}, S_{22}, S_{21}$)**: **Critical.** Verification of Input Return Loss ($S_{11} < -10\text{dB}$), Output Return Loss, and Transducer Gain.
        * **Noise Figure (NF)**: **Critical.** Measured in dB, accounting for source thermal noise.
        * **Stability ($K$-Factor/$\mu$-Factor)**: Stern stability analysis to ensure unconditional stability ($K>1$).
        * **Linearity ($IIP3 / P_{1dB}$)**: Two-tone test.
* **Topologies**:
    * **Inductively Degenerated Common-Source**:  The industry standard LNA topology using a source inductor to generate a real input impedance part ($50\Omega$) without adding noise.
    * **Common-Gate (CG)**: Broad-band input matching ($1/g_m$) often used for wideband applications.
    * **Resistive Feedback (Shunt-Shunt)**: For wideband matching at the cost of Noise Figure.
* **Rule**: The circuit is an **RF SISO Block**.
    * **Condition:** Must contain RF matching components (inductors, T-coils, matching capacitors) or be intended for $50\Omega$ environments.
    * **Strict Exclusion:** If the circuit performs Single-to-Differential conversion (Active Balun), it is **Class 20**. Class 38 output is always single-ended.

### 39. Output Drivers & Power Amplifiers (Push-Pull / Class B / AB)
High-current driver stages designed to drive low-impedance loads (speakers, transmission lines, antennas) or capacitive loads. These circuits operate in the "large-signal" regime where **efficiency** and **crossover distortion** are the dominant concerns.

* **Ports:**
    * **Required:** Input (may be single-ended or split complementary inputs for High-Side/Low-Side driving).
    * **Required:** Output (High current capability / Low $Z_{out}$).
* **Stimuli/Measurements:**
    * **Stimuli:** Large-signal Sine Wave (close to rail-to-rail) or Pulse train.
    * **Measurements:**
        * **Total Harmonic Distortion (THD):** **Critical.** Transient analysis + Fourier Transform (FFT) to detect crossover distortion and clipping. Small-signal AC analysis hides these faults.
        * **Efficiency (PAE / Drain Eff):** Measurement of Power Out vs. DC Power Consumed.
        * **Load-Pull:** (For RF PAs) Varying load impedance to find optimal power/efficiency contours.
        * **Quiescent Current:** DC sweep to tune the "dead zone" in Class AB stages.
* **Topologies:**
    * **Push-Pull Output Stages:** Class B, Class AB (using diode-connected biasing or $V_{be}$ multipliers).
    * **Complementary Drivers:** CMOS Inverter-based amplifiers (used as analog drivers), Quasi-Complementary (NPN+NPN) stages.
    * **Source/Emitter Followers:** Specifically large-device buffers intended for current gain (Current Buffers).
* **Rule:** The circuit utilizes **complementary devices** (N-type and P-type) or split paths to fundamentally handle **sourcing and sinking current** separately.
    * Identified by a "totem-pole" output structure.
    * Distinguished from Class 1 by the requirement for THD/FFT analysis rather than just Phase Margin.


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

