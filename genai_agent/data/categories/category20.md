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