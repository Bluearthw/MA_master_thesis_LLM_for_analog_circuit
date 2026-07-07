

## **DOI:10.1587/transele.2025CDP0005** 

**Publicized:2025/12/22** 

**This article has been accepted and published on J-STAGE in advance of copyediting. Content is final as presented.** 



IEICE TRANS. ELECTRON., VOL.Exx–??, NO.xx XXXX 200x 

1 

# <u>PAPER</u> _Special Section on Solid-State Circuit Design—Architecture, Circuit, Device and Design Methodology_ **Efficient Analog Circuit Sizing with Domain-Guided Sampling and Fidelity-Adaptive Simulation** 

**Yuto MORIGUCHI**<sup>†a)</sup> **,** **_Nonmember and_ Nobukazu TAKAI**<sup>†b)</sup> **,** **_Member_** 

**SUMMARY** Analog circuit sizing remains a challenging task owing to nonlinear behavior, complex trade-offs, sensitivity to PVT variations, and the high computational cost of transistor-level simulations. To address these issues, we propose a simulation-efficient analog circuit sizing approach that adaptively adjusts simulation fidelity according to the design stage. The method operates in of two stages: an initial sampling phase using fast operating point analysis to identify high-quality design candidates, followed by a Bayesian optimization phase that refines these candidates using highfidelity simulations. A Sobol sequence is employed to generate uniformly distributed design points, and domain knowledge is integrated into the lowfidelity evaluations to guide sampling toward feasible and high-performing regions. Experimental validation on an operational amplifier designed using the TSMC 180nm CMOS process shows that the proposed method reduces the number of optimization iterations required to find a feasible solution to 40% of that of the conventional approach. Furthermore, the proposed method yields designs with improved DC gain and lower power consumption in constrained optimization scenarios, confirming the benefit of domain-informed sampling. These results suggest that incorporating domain knowledge into fidelity-adaptive optimization is a promising direction for scalable and interpretable analog circuit design automation. **_key words:_** _Analog Circuit, Bayesian Optimization, Operational amplifiers, Analog Circuit Sizing Automation_ 

### **1. Introduction** 

As transistor dimensions continue to shrink, analog integrated circuit (IC) design has become increasingly challenging. The inherent nonlinearity, complex trade-offs among performance metrics, sensitivity to variations, and the computational cost of transistor-level simulations all serve as major obstacles in the automation of analog electronic design automation (EDA). The increasing demand for reduced time-to-market has further fueled interest in automating analog circuit design. Among the various research directions, considerable attention has been given to automating the optimization of device parameters (such as transistor length and width) commonly referred to as “analog circuit sizing.” Various approaches have been proposed for analog circuit sizing automation, starting from knowledge-based methods[1], [2] and evolving toward simulation-based techniques such as particle swarm optimization[3], simulated annealing[4], and genetic algorithms[5]. More recently, the application of machine learning has emerged as one of the most promising directions in analog circuit design automation, specifically 

> †Department of Electronics, Kyoto Institute of Technology Hashikamicho, Matsugasaki, Sakyo-ku, Kyoto 606-8585, Japan a) E-mail: ymoriguchi@vlsi.es.kit.ac.jp b) E-mail: takai@kit.ac.jp 

by utilizing techniques such as deep reinforcement learning (DRL)[6] and Bayesian optimization (BO), which have demonstrated remarkable success in other domains. 

In knowledge-based methods, the design process follows rules defined by expert designers to generate circuits that meet the target specifications. Although this approach can produce valid designs, it requires considerable effort to encode expert knowledge into rules. Conversely, simulationbased methods explore optimal designs by generating candidate circuits through algorithms and evaluating them using circuit simulators such as SPICE. These methods treat the internal circuit behavior as a black box, thereby reducing the interpretability of the resulting designs. Moreover, the extensive simulations required during the search process incur a significant computational cost, particularly considering process, voltage, and temperature (PVT) variations[7]–[9] or layout-induced effects[10], [11]. Various methods have been proposed to alleviate the simulation overhead, with surrogate modeling[12], [13] and selective simulation strategies[10], [14] being among the most prevalent. 

Recent studies have also proposed hybrid approaches that combine knowledge- and simulation-based methodologies[15]–[18]. For instance, rule-guided genetic algorithms (RG-GA)[15] enhance the search efficiency of genetic algorithms by incorporating design rules into the mutation process. Other recent frameworks, including ADO-LLM[16] and LEDRO[17], successfully integrate domain knowledge extracted from large language models (LLMs) into BO, effectively combining the guidance of knowledge-based rules with the powerful search capabilities of simulation-based methods. 

In this study, we propose a method that improves both the efficiency and interpretability of simulation-based analog circuit design automation by incorporating knowledge-based techniques into the initial sampling process. 

The remainder of this paper is organized as follows. Section 2 defines the analog circuit sizing problem and provides an overview of machine learning-based approaches. Section 3 presents the proposed hybrid design automation methodology that integrates knowledge- and simulationbased techniques. Section 4 demonstrates the application of the method to op-amp design. Finally, conclusions are presented in Section 5. 

Copyright © 200x The Institute of Electronics, Information and Communication Engineers 

IEICE TRANS. ELECTRON., VOL.Exx–??, NO.xx XXXX 200x 

2 

be reformulated into a reward function as in Equation (3): 

### **2. Background and Related Work** 

### 2.1 Problem Formulation 

In analog circuit sizing automation, two primary formulations are used to define design objectives. One approach formulates the problem as a constrained optimization problem[10], [12], [19]–[21] in which an objective function is optimized subject to a set of constraints. The other approach formulates it as a constraint satisfaction problem (CSP) [8], [16], [22], [23] in which all design specifications are treated as constraints, and candidate solutions are evaluated solely based on whether they satisfy all these constraints. 

In the former approach, analog circuit sizing is formulated as the following constrained optimization problem: 



Here, _𝑥_ ∈ R<sup>_𝑛_</sup> is a vector of design variables, including the sizes of transistors, capacitors, and resistors. The goal is to find a design _𝑥_ that maximizes or minimizes the objective function _𝑓_ ( _𝑥_ ) while satisfying the inequality constraints _𝑔𝑖_ ( _𝑥_ ) and equality constraints _ℎ 𝑗_ ( _𝑥_ ). 

In machine learning–based automatic sizing, a figure of merit (FoM) is generally introduced to convert the constrained optimization problem into a single scalar objective. In this study, the FoM is defined as 



Here, _𝑤𝑛_ denotes weighting coefficients used to evaluate multiple performance metrics with different scales, and ˆ· indicates normalization. Constraint values are clipped when the constraints are satisfied. Scalarization facilitates the application of optimization algorithms by transforming the multi-objective, constrained problem into a single-objective form. However, this approach also introduces ambiguity between “objectives” and “constraints,” potentially blurring the distinction between the two. 

Conversely, the latter approach specifies explicit design requirements for all circuit performance metrics and evaluates candidate solutions solely based on whether all these specifications are satisfied. This formulation does not include an objective function and is treated as a pure constraint satisfaction problem. This approach is particularly effective in product development and mass production design phases, where design requirements are well-defined and clearly specified. However, this approach has certain limitations. When no feasible solution exists, the optimization process may stagnate. Moreover, the method provides little guidance for navigating trade-offs or improving the design. Nevertheless, by defining the degree of specification satisfaction in a continuous manner, meaningful feedback can be provided to optimization algorithms, even within a constraint satisfaction framework. For instance, by normalizing the error or relative achievement with respect to the specification values and aggregating them in a weighted form, the problem can 



Such an approach enables the generation of informative guidance during the exploration of the design space, allowing for more flexible and effective design automation beyond the traditional constraint satisfaction paradigm. 

### 2.2 Analog Circuit Sizing Automation 

Analog circuit sizing automation can be broadly classified into two main paradigms: knowledge-based methods and simulation-based methods. Each approach exhibits distinct characteristics, with complementary strengths and weaknesses. 

Knowledge-based methods are grounded in the idea of formalizing the expertise accumulated by human designers over years of practice into design rules or analytical models, and leveraging them for automated design. OPASYN[1] determines transistor dimensions by applying standardized design rules to each building block of an operational amplifier, such as the differential pair, current mirror, and compensation stage. These rules may include operating transistors in the saturation region or maintaining specific sizing ratios to ensure a desired gain. A major advantage of this approach lies in its computational efficiency, enabling rapid execution. Furthermore, the resulting circuits tend to be structurally meaningful and highly interpretable because the design intent is explicitly embedded in the rules. However, knowledge-based methods also face fundamental limitations. First, the rules and models used are generally tailored to specific process technologies and circuit topologies. Consequently, adapting them to new architectures or advanced nodes necessitates substantial redesign of the rule set, posing challenges in scalability and maintainability. Second, as these models approximate real device behavior, their accuracy deteriorates in deep-submicron and beyond, where process scaling introduces complex effects. In such cases, discrepancies between the model predictions and circuit simulations become non-negligible. 

In response to the limitations of knowledge-based methods, the simulation-based approach has garnered increasing attention and has undergone significant development. In this approach, the designed circuit is directly evaluated using SPICE simulations, and its performance is used to guide the search for optimal parameters through optimization algorithms such as genetic algorithms or simulated annealing. In contrast to those that rely on designer knowledge, this method iteratively improves the circuit based on actual performance measurements. Consequently, it is theoretically applicable to any topology. Moreover, the evaluation closely reflects real circuit behavior, rendering the results highly reliable. The key strengths of this approach lie in its versatility and accuracy. Free from rigid design rules, this approach can be applied to a wide range of circuit architectures within 

MORIGUCHI and TAKAI: EFFICIENT ANALOG CIRCUIT SIZING WITH DOMAIN-GUIDED SAMPLING AND FIDELITY-ADAPTIVE SIMULATION 

3 

a unified framework, offering broad applicability. Furthermore, it naturally accounts for effects that are difficult to handle in knowledge-based methods, such as process variations and post-layout parasitics, through direct simulation. Nevertheless, the major drawback of this method is the high computational cost. Typically, numerous evaluations are required, and each SPICE simulation can be time-consuming, leading to longer overall design times. Additionally, the resulting optimized designs are often difficult to interpret, rendering understanding the rationale behind the outcomes or reflecting explicit design intent challenging. 

In recent years, hybrid approaches that combine the strengths of both knowledge-based and simulation-based methods have gained considerable attention[15]–[18]. RGGA[15] exemplifies this trend by enhancing conventional genetic algorithms with domain-specific design knowledge. Instead of relying solely on random mutation and crossover, RG-GA incorporates knowledge-driven guidance to improve search efficiency and strike a balance between performance and design intent. For example, a rule such as “if the gain is too low, increase the W/L ratio of the load transistor” can be embedded into the mutation process, enabling more meaningful control over the search direction. This type of strategy is well-suited for scenarios in which broad, global exploration is desirable in the early stages of optimization, followed by more targeted, knowledge-driven refinement in later stages. 

The challenge of manually defining domain-specific rules in knowledge-based methods can now be addressed through the use of LLMs, which have seen remarkable progress in recent years. Recent studies have demonstrated that even vanilla LLMs can leverage domain knowledge to improve the sample efficiency of automated design processes[16]. Furthermore, techniques such as retrievalaugmented generation (RAG) have been proposed to further enhance LLMs with external domain knowledge[24]–[26], rendering the integration of expert insights into design automation significantly more accessible than before. 

Various strategies have been proposed to address the high computational cost of simulations, a common limitation in simulation-based methods. These approaches can be broadly classified into surrogate modeling techniques[12], [13] and multi-fidelity simulation methods[10], [14]. 

Many analog circuit sizing automation methods employ neural networks or Gaussian Process (GP) regression models to infer circuit performance metrics or FoM from design variables. These models effectively serve as internal surrogates for circuit simulators. Surrogate modeling approaches face a significant limitation: they require a substantial number of data points to develop precise models. Current methods remain insufficient despite techniques such as synthetic sample generation[19] and transfer learning[12] having been proposed to improve efficiency. 

Multi-fidelity simulation methods adjust the type of simulation according to the design stage. This approach is particularly useful in analog sizing tasks that consider PVT variations or layout-dependent effects. Typical strategies 

include excluding low-priority PVT corners during training[8], [9] and learning the correlation between simulation results of varying fidelity levels[10], [14]. 

Although both adaptive simulation-selection algorithms and LLM-based domain knowledge extraction have been independently explored, existing approaches suffer from fundamental limitations. Adaptive simulation methods typically rely on surrogate models to compensate for the reduced information obtained from low-fidelity simulations, which introduces additional computational overhead and uncertainty. On the other hand, LLM-driven knowledge embedding methods often incur high computational cost due to the expensive inference required to extract and utilize domain knowledge. 

In this work, we address these limitations by integrating adaptive simulation selection with domain knowledge embedding, enabling efficient and stable analog circuit design. By injecting human-interpretable domain constraints in the low-fidelity stage, the proposed method compensates for the lack of information without relying on computationally expensive neural models or repeated LLM inference. This unified approach provides a new balance between computational efficiency, search quality, and design interpretability. 

### **3. Method** 

This section proposes an efficient analog circuit sizing method that combines simulation cost reduction by selecting simulation type according to the design stage, with a sampling strategy guided by designer knowledge. The proposed method comprises two stages: 

- Selection of high-quality samples using operating point analysis 

- Bayesian optimization based on full-performance simulations 

In the first stage, fast operating point analysis is used to distinguish between functionally valid and invalid designs. Only valid designs are selected as high-quality samples and passed to the Bayesian optimization stage. The overall optimization flow is illustrated in Algorithm 1. 

**Algorithm 1** Overall Flow of the Proposed Method 

|1:|Get initial sample set_𝑋_init of _𝑁_init designs|
|---|---|
|2:|Get low-fdelity metrics _𝑓_1(_𝑋_init)|
|3: <br>|Choose _𝑁_elite elite designs_𝑋_elite ⊂_𝑋_init<br>|
|4:|Get high-fdelity metrics _𝑓_2(_𝑋_elite)|
|5:|**for**_𝑖_=1_,_2_, ..., 𝑁_max **do**|
|6:|Fit GP model|
|7:|Get new design varialbes_𝑋𝑖_|
|8:|Get high-fdelity metrics _𝑓_2(_𝑋𝑖_)|
|9:|**if** _𝑓_2(_𝑋𝑖_) are met**and**Problem is CSP**then**|
|10:|_𝑁_total =_𝑖_|
|11:|Break|
|12:|**end if**|
|13:|**end for**|
|14:|**return** Design with the highest FoM|



IEICE TRANS. ELECTRON., VOL.Exx–??, NO.xx XXXX 200x 

4 

and accurate evaluations _𝑓_ 2 ( _𝑋_ elite) are obtained. 

### 3.1 Initial Sampling using Low-Fidelity Simulation 

Analog circuit sizing can be divided into two distinct phases: making the circuit function correctly and maximizing its performance. Each phase requires different types of circuit simulations. For instance, determining whether a circuit is functionally operational can often be achieved using low-cost analyses like operating point analysis or DC analysis. Conversely, detailed performance evaluation typically requires high-cost simulations, such as transient analysis. Many existing analog circuit sizing methods rely solely on high-fidelity testbenches for performance evaluation throughout the entire optimization process. Even methods that incorporate variable simulation fidelity primarily focus on adjusting the fidelity during the performance maximization phase. In early design stages, optimization algorithms typically generate invalid or non-functional designs. Identifying such infeasible candidates through low-cost simulations, such as operating point analysis, can significantly reduce the overall computational load of circuit evaluation. 

Low-fidelity simulation is performed using operating point analysis to determine whether a circuit is functionally valid based on transistor operating regions and node voltages (lines 1 and 2 of Algorithm 1). Operating point analysis is significantly faster than other types of simulation, enabling a larger number of samples to be evaluated compared to highfidelity tests. Furthermore, the candidate generation process must also be computationally inexpensive to fully utilize the efficiency of low-cost operating point analysis. In practice, the modeling time required for Bayesian optimization often exceeds the runtime of operating point analysis by an order of magnitude. Furthermore, applying an optimization algorithm at this stage increases the risk of convergence to local optima because the information obtained from lowfidelity analysis is limited compared to that in high-fidelity evaluation. To overcome this constraint, candidate points for low-fidelity simulation are generated using a Sobol sequence[27]. The Sobol sequence is a quasi-Monte Carlo sampling method that distributes points uniformly across the design space, enabling the generation of well-spread samples even in high-dimensional spaces. 

The termination condition for optimization varies depending on the target problem. In the case of constrained optimization problems, the BO loop continues until the maximum number of iterations _𝑁_ max is reached, and the objective _𝑓_ 2 is either maximized or minimized. For constraint satisfaction problems (CSPs), the loop terminates once a design satisfying all required specifications is found. In this case, the total number of BO iterations is denoted by _𝑁_ total. Even in CSPs, the search is terminated when _𝑁_ max is reached. This upper limit is imposed to prevent excessive computational cost due to the cubic scaling of BO modeling time with the number of samples. 

### 3.3 Embedding Domain Knowledge 

Operating point analysis of MOSFETs provides not only information about operating regions but also various internal parameters, as summarized in Table 1. In analog circuit design, quantities such as the voltage differences between terminals ( _𝑣_ gs- _𝑣_ bs), terminal currents ( _𝑖_ d- _𝑖_ bd), and transconductance ( _𝑔_ m) are of particular importance. For example, the total supply current can be estimated by summing the drain currents ( _𝑖_ d) of MOSFETs across the circuit. Additionally, one may increase the _𝑔_ m of transistors contributing to amplification to improve gain or bandwidth. These examples illustrate that the experience and intuition of analog designers are closely tied to quantities obtainable from operating point analysis. Domain knowledge can be directly incorporated into the sampling process itself by integrating evaluation metrics derived from domain knowledge, either provided by human designers or large language models, into the low-fidelity sampling stage. 



### **4. Experiments** 

### 4.1 Experiment Setup and Algorithm Settings 

### 3.2 Bayesian Optimization Based on Elite Samples 

Bayesian optimization is performed using only the designs identified as high-quality through low-fidelity simulation (line 3 onward in Algorithm 1). Although Bayesian optimization is efficacious at finding optimal solutions from a small number of samples, it suffers from high computational complexity: the modeling cost scales as O( _𝑁_<sup>3</sup> ) with respect to the number of samples _𝑁_ , resulting in rapidly increasing computational demands as _𝑁_ grows. In the proposed method, only high-quality design data are passed to the optimization algorithm, thereby enhancing search performance while reducing runtime. High-fidelity simulations are conducted for the selected high-quality samples _𝑋_ elite, 

The proposed method is applied to the automatic sizing of the operational amplifier (Figure 1) to evaluate the sample efficiency achieved through low-fidelity simulation and the effectiveness of embedded domain knowledge. The design includes 17 variables, with their respective upper and lower bounds listed in Table 2. The operational amplifier is designed using the TSMC 180nm CMOS process, and all simulations are performed under nominal PVT conditions, with a supply voltage of 1.8 V, a temperature of 25<sup>◦</sup> C, and a load capacitance of 100 pF. 

The automatic design algorithm, Bayesian optimization, was implemented using BoTorch[28] and GPyTorch[29], with the Sobol Engine[27] used for generating 

MORIGUCHI and TAKAI: EFFICIENT ANALOG CIRCUIT SIZING WITH DOMAIN-GUIDED SAMPLING AND FIDELITY-ADAPTIVE SIMULATION 

5 



<!-- Start of picture text -->
M6 M7<br>M5<br>M3 M4<br>M1 M2<br>M0<br>Fig. 1 Target Operational Amplifier<br><!-- End of picture text -->

the Sobol sequence. Circuit simulations were performed using Synopsys, HSPICE. All experiments were conducted on a Linux server equipped with an Intel Xeon Gold 6426Y processor and 1 TB of RAM. 

We conducted three experiments to validate the effectiveness of the proposed method. First, we analyzed the difference in computational cost caused by varying simulation fidelity and evaluated the resulting sample efficiency. Second, we compared and evaluated the efficiency of the algorithm when analog circuit sizing is formulated as a constraint satisfaction problem (CSP). Third, we assessed the algorithm’s efficiency when the sizing problem is formulated as a constrained optimization problem. In the third experiment, we quantified the improvement in the final design quality achieved by embedding domain knowledge into the low-fidelity simulation evaluation. 

**Table 2** Design variables and ranges 

|Variable Name|Unit|Lower Limit|Upper Limit|
|---|---|---|---|
|MOSFET Length|µm|0.18|2.0|
|MOSFET Width|µm|0.22|10.0|
|MOSFET Finger|-|2|16|
|Capacitance|fF|35.6|1791.9|
|Resistance|kΩ|1.12|530|
|Bias Current|µA|0.01|10.0|



### 4.2 Sample Efficiency 

We first compared and evaluated the simulation time under different fidelity settings. The circuit performance metrics considered in this experiment are summarized in Table 3. High-fidelity simulation evaluates all performance metrics and comprises operating point analysis, three AC analyses, DC analysis, and transient analysis. Conversely, low-fidelity simulation performs only operating point analysis. 

Table 4 compares the CPU time required for simulations with different fidelities. Operating point analysis alone was 17.8 times faster than the full simulation that evaluates all performance metrics. 

Let _𝑁_<sup>highthenumberofinitialsampleswhen</sup> init<sup>denote</sup> using only high-fidelity simulations. Then, the number of initial samples when using low-fidelity simulation, _𝑁_ init<sup>multi, is</sup> defined as follows: 

**Table 3** Evaluated circuit performance metrics 

|Metric|Analysis|Description|
|---|---|---|
|# of Sat.|OP|Number of MOSFETs operating in saturation|
|DC Gain|AC(1)|DC gain|
|UGF|AC(1)|Unity-gain frequency|
|PM|AC(1)|Phase margin|
|GM|AC(1)|Gain margin|
|_𝐼_total|DC|Current consumption|
|O. Swing|DC|Output voltage swing|
|Ofset|DC|Output ofset voltage|
|CMRR|AC(2)|Common-mode rejection ratio|
|PSRR|AC(3)|Power supply rejection ratio|
|Settling|TRAN|Settlingtime|



|**Table 4**|Simulation Time Compari|son|
|---|---|---|
||All Metrics|OP Only|
|Analyses|OP, AC, DC, Transient|OP|
|Sim. Time [ms]|598.56|33.57|
|Efciency|×1|×17.8|



This reflects the fact that operating point analysis is 17.8 times faster than full evaluation, enabling more samples to be assessed within the same computational budget. 

### 4.3 Search Efficiency in Constraint Satisfaction Problems (CSP) 

A constraint satisfaction problem (CSP) is implemented using Bayesian optimization, where the goal is to satisfy all performance targets defined for each metric listed in Table 3. The specific targets for each metric are summarized in Table 5. As each target has a different optimization direction (i.e., to be maximized or minimized), the weight _𝑤𝑖_ in Equation (eq:csp) is assigned a positive or negative sign so that the product _𝑤𝑖_ × _𝑔_ ˆ _𝑖_ ( _𝑥_ ) = 1 when the target is met. Consequently, if all 11 targets are satisfied, the total reward becomes Reward = 11. The computed Reward in Equation (3) is passed to Bayesian optimization as the objective function _𝑓_ 2 in Algorithm 1. 

**Table 5** CSP problem definition 

|Metric|Target|Metric|Target|
|---|---|---|---|
|# of Sat.|=8|Out. Swing|_>_0_._95_𝑉𝐷𝐷_|
|DC Gain|_>_60 dB|Ofset|_<_1_._5 mV|
|UGF|_>_2 MHz|CMRR|_>_60 dB|
|PM|_>_45<sup>◦</sup>|PSRR|_>_60 dB|
|GM|_>_10 dB|Settling|_<_2.5µs|
|_𝐼_total|_<_350 µA|||



Evaluation using low-fidelity simulation based on operating point analysis is performed according to Equation (5). The Reward in Equation (5) is used as _𝑓_ 1 in Algorithm 1. During the initial sampling phase, the top _𝑁_ elite samples with the highest _𝑓_ 1 values are selected and passed to the Bayesian optimization stage. The parameters used for Bayesian optimization are summarized in Table 6. 



(5) 

Reward = # of Saturation MOSFET 

IEICE TRANS. ELECTRON., VOL.Exx–??, NO.xx XXXX 200x 

6 



<!-- Start of picture text -->
10.0<br>9.8<br>9.6<br>9.4<br>9.2<br>9.0<br>8.8<br>8.6 High-Fidelity<br>Multi-Fidelity<br>8.4<br>50 100 150 200 250 300<br>Ninit<br>Figure of Merit f2<br><!-- End of picture text -->

**Fig. 2** Result of initial sample efficiency 

The evaluation results _𝑓_ 2 ( _𝑋_ elite) for the elite samples selected from the initial Sobol sequence are illustrated in Figure 2. For comparison, the results obtained using only high-fidelity simulations for the initial sampling are also presented. To ensure a fair comparison, we adjusted the number of initial samples _𝑁_ init using Equation (4) so that the two methods have similar computational costs. In the highfidelity-only setting, the evaluation score decreases as the number of initial samples decreases. Conversely, the initial samples obtained through low-fidelity simulation maintain a certain level of design quality, even under a computational budget equivalent to just 15 high-fidelity simulations. In the case of low-fidelity initial sampling, _𝑓_ 2 remains constant when _𝑁_ init exceeds 100. This behavior is attributed to the deterministic nature of the Sobol sequence: as the number of samples increases, the same designs tend to be selected as _𝑋_ elite. This saturation does not appear in the high-fidelityonly case because each high-fidelity simulation yields more detailed information, enabling more fine-grained evaluation of each design candidate. 

**Table 6** Bayesian optimization parameters (CSP) 

||Multi-Fidelity<br>High-Fidelity|
|---|---|
|_𝑁_|5160, 3387, 1604<br>300, 200, 100|
|init|1158, 713, 89<br>75, 50, 15|
|_𝑁_elite|10|
|_𝑁_max|100|
|Acquisition|LogEI[30]|
|Batch Size|4|



Next, we compared the number of Bayesian optimization iterations _𝑁_ total required to find a design that satisfies all constraints. Each setting of the initial sample size was tested five times to account for the stochastic nature of BO. The average result is presented in Figure 3. In the case of using only high-fidelity simulations for the initial samples, reducing the number of samples renders finding a feasible design increasingly difficult. Conversely, initial sampling with lowfidelity simulations demonstrates greater robustness against reductions in _𝑁_ init. The 0.4× reduction in the average number of evaluations was obtained under the setting with the smallest initial sample size. 



<!-- Start of picture text -->
60<br>High-Fidelity<br>55 Multi-Fidelity<br>50<br>45<br>40<br>35<br>30<br>25<br>50 100 150 200 250 300<br>Ninit<br>total<br>N<br><!-- End of picture text -->

**Fig. 3** Result of CSP Automatic Sizing Performance _𝑁_ total 

- 4.4 Embedding Domain Knowledge in Constrained Optimization 

The circuit illustrated in Figure 1 is automatically sized by formulating the task as a constrained optimization problem, as defined in Equation 6. Similar to CSP, FoM is transformed into a maximization objective through appropriate weighting. 



Evaluation using low-fidelity simulation based on operating point analysis is performed according to Equation (7). As the final design objective is to minimize power consumption, the method aims to minimize the drain currents of the three tail current sources (M0–M2) in the circuit shown in Figure 1. Simultaneously, the method also seeks to maximize the transconductance of M3, M4, and M7, which are responsible for signal amplification, to ensure that the circuit functions as an operational amplifier. 



**Table 7** Bayesian optimization parameters (COP) 

||Multi-Fidelity|High-Fidelity|
|---|---|---|
|_𝑁_init|106, 195, 284, ..., 1352|26, 31, 36, ..., 96|
|_𝑁_elite|20||
|_𝑁_max|100||
|Acquisition|LogEI[30]||
|Batch Size|4||



The parameters used for BO are shown in Table 7. The 

MORIGUCHI and TAKAI: EFFICIENT ANALOG CIRCUIT SIZING WITH DOMAIN-GUIDED SAMPLING AND FIDELITY-ADAPTIVE SIMULATION 

7 



<!-- Start of picture text -->
12.25<br>12.00<br>11.75<br>11.50<br>11.25<br>11.00<br>10.75 High-Fidelity<br>Multi-Fidelity<br>10.50<br>30 40 50 60 70 80 90<br>Ninit<br>Fig. 4 Result of initial sample efficiency<br>1.2<br>High-Fidelity<br>( =14.89, =0.40)<br>1.0 Multi-Fidelity<br>( =15.02, =0.32)<br>0.8<br>0.6<br>0.4<br>0.2<br>0.0<br>14.0 14.5 15.0 15.5<br>Figure of Merit f2<br>Figure of Merit f2<br>Density<br><!-- End of picture text -->

**Fig. 5** Comparison of FoM distributions (KDE-based visualization) 

evaluation _𝑓_ 2 ( _𝑋_ elite) of the elite samples selected from the Sobol sequence is shown in Figure 4. As observed in Figure 2, the evaluation score decreases with fewer samples when only using high-fidelity simulations. Conversely, initial sampling based on low-fidelity simulations yields designs with consistent performance, even under limited computational cost. 

Figure 5 presents the comparison of FoM distributions over 500 runs for both the proposed method and the conventional high-fidelity baseline. The proposed method not only yields a higher mean FoM but also significantly improves robustness. The coefficient of variation is reduced from 0.027 to 0.021, demonstrating markedly more stable optimization behavior. The final designs obtained by each method are compared in Table 8. In the proposed method, the initialization strategy selects designs with a high DC gain using eq.(7). As a consequence, the optimized solutions tend to assign larger channel lengths to transistors such as M2 and M5-6. These longer channel devices exhibit higher output resistance, thereby enabling the proposed method to achieve designs with higher DC gain and CMRR. Furthermore, with respect to the optimization objective of power consumption, the proposed method reduces power relative to the conventional method. 

### **5. Conclusion** 

This study proposed a hybrid framework for analog circuit 

**Table 8** Performance Comparison of Final Designs 

|Metric|High-Fidelity|Multi-Fidelity|
|---|---|---|
|DC Gain|60.8 dB|64.74 dB|
|PM|55_._9<sup>◦</sup>|53_._4<sup>◦</sup>|
|Power|15.8µW|14.7µW|
|Ofset|0.14 mV|0.50 mV|
|CMRR|77.7 dB|79.68 dB|
|PSRR|61.7 dB|62.6 dB|
|Settling|239 ns|231 ns|
|Parameter|High-Fidelity|Multi-Fidelity|
|M0, M1, M2 Length [µm]|1.26|2.00|
|M0, M1, M2 Width [µm]|0.22|0.22|
|M0 Finger|2|2|
|M1 Finger|8|4|
|M2 Finger|12|4|
|M3, M4 Length [µm]|0.18|0.18|
|M3, M4 Width [µm]|0.22|0.22|
|M3, M4 Finger|2|2|
|M5, M6 Length [µm]|1.10|1.63|
|M5, M6 Width [µm]|0.22|0.22|
|M5, M6 Finger|8|16|
|M7 Length [µm]|0.18|0.18|
|M7 Width [µm]|0.69|0.22|
|M7 Finger|2|4|
|Capacitance [fF]|35.6|35.6|
|Resistnce [kΩ]|9.57|53.0|
|Bias Current[µA]|0.75|1.60|



sizing that integrates low-fidelity simulation, domain knowledge, and high-fidelity optimization. Low-fidelity simulations in the proposed method enable early exclusion of invalid designs and allow for the integration of domain knowledge. Experiments on an operational amplifier demonstrate up to 0.4× improvement for constraint satisfaction and better final performance in constrained optimization. 

These results highlight the potential of fidelity-adaptive simulation and domain-informed sampling for scalable and effective analog design automation. 

### **Acknowledgments** 

This work was supported by JST Moonshot R&D Program Grant Number JPMJMS226A. 

#### **References** 

- [1] H. Koh, C. Sequin, and P. Gray, “Opasyn: a compiler for cmos operational amplifiers,” IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems, vol.9, no.2, pp.113–125, 1990. 

- [2] N. Jangkrajarng, S. Bhattacharya, R. Hartono, and C.J.R. Shi, “Iprail: intellectual property reuse-based analog ic layout automation,” Integr. VLSI J., vol.36, no.4, p.237–262, Nov. 2003. 

- [3] M. Fakhfakh, Y. Cooren, A. Sallem, M. Loulou, and P. Siarry, “Analog circuit design optimization through the particle swarm optimization technique,” Analog Integr. Circuits Signal Process., vol.63, no.1, p.71–82, 4 2010. 

- [4] M. Hershenson, S. Boyd, and T. Lee, “Optimal design of a cmos opamp via geometric programming,” IEEE Transactions on ComputerAided Design of Integrated Circuits and Systems, vol.20, no.1, pp.1– 21, 2001. 

- [5] W. Kruiskamp and D. Leenaerts, “Darwin: Cmos opamp synthesis by means of a genetic algorithm,” Proceedings of the 32nd Annual ACM/IEEE Design Automation Conference, DAC ’95, New York, 

IEICE TRANS. ELECTRON., VOL.Exx–??, NO.xx XXXX 200x 

8 

USA, p.433–438, Association for Computing Machinery, 1995. 

- [6] K. Settaluri, A. Haj-Ali, Q. Huang, K. Hakhamaneshi, and B. Nikolic, “Autockt: Deep reinforcement learning of analog circuit designs,” 2020 Design, Automation & Test in Europe Conference & Exhibition (DATE), pp.490–495, 2020. 

- [7] W. Cao, J. Gao, T. Ma, R. Ma, M. Benosman, and X. Zhang, “Roseopt: Robust and efficient analog circuit parameter optimization with knowledge-infused reinforcement learning,” IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems, vol.44, no.2, pp.627–640, 2025. 

- [8] W. Shi, H. Wang, J. Gu, M. Liu, D.Z. Pan, S. Han, and N. Sun, “Robustanalog: Fast variation-aware analog circuit design via multitask rl,” 2022 ACM/IEEE 4th Workshop on Machine Learning for CAD (MLCAD), pp.35–41, 2022. 

- [9] Z. Kong, X. Tang, W. Shi, Y. Du, Y. Lin, and Y. Wang, “Pvtsizing: A turbo-rl-based batch-sampling optimization framework for pvtrobust analog circuit synthesis,” Proceedings of the 61st ACM/IEEE Design Automation Conference, DAC ’24, New York, USA, Association for Computing Machinery, 2024. 

- [10] A.F. Budak, K. Zhu, and D.Z. Pan, “Practical layout-aware analog/mixed-signal design automation with bayesian neural networks,” 2023 IEEE/ACM International Conference on Computer Aided Design (ICCAD), pp.1–8, 2023. 

- [11] X. Gao, H. Zhang, S. Ye, M. Liu, D.Z. Pan, L. Shen, R. Wang, Y. Lin, and R. Huang, “Post-layout simulation driven analog circuit sizing,” 2023. 

- [12] Y. Wang, J. Xin, H. Liu, Q. Qin, C. Chai, Y. Lu, J. Hao, J. Xiao, Z. Ye, and Y. Wang, “Dc-model: A new method for assisting the analog circuit optimization,” 2023 24th International Symposium on Quality Electronic Design (ISQED), pp.1–7, 2023. 

- [13] Z. Gao, J. Tao, F. Yang, Y. Su, D. Zhou, and X. Zeng, “Efficient performance trade-off modeling for analog circuit based on bayesian neural network,” 2019 IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp.1–8, 2019. 

tions on Computer-Aided Design of Integrated Circuits and Systems, vol.41, no.1, pp.1–14, 2022. 

   - [22] H. Wang, K. Wang, J. Yang, L. Shen, N. Sun, H.S. Lee, and S. Han, “Gcn-rl circuit designer: Transferable transistor sizing with graph neural networks and reinforcement learning,” 2020 57th ACM/IEEE Design Automation Conference (DAC), pp.1–6, 2020. 

   - [23] T. Masubuchi and N. Takai, “Op-amp sizing with large number of design variables using turbo,” 2024 IEEE Asia Pacific Conference on Circuits and Systems (APCCAS), pp.649–653, 2024. 

   - [24] J. Wu, M. Wang, J. Jeong, and L. Jiao, “Adaptive-distributed arithmetic coding for lossless compression,” 2010 2nd IEEE InternationalConference on Network Infrastructure and Digital Content, pp.541–545, 2010. 

   - [25] H. Zhang, S. Sun, Y. Lin, R. Wang, and J. Bian, “Analogxpert: Automating analog topology synthesis by incorporating circuit design expertise into large language models,” 2025. 

   - [26] Y. Lai, S. Lee, G. Chen, S. Poddar, M. Hu, D.Z. Pan, and P. Luo, “Analogcoder: Analog circuit design via training-free code generation,” 2024. 

   - [27] S. Joe and F.Y. Kuo, “Constructing sobol sequences with better twodimensional projections,” SIAM Journal on Scientific Computing, vol.30, no.5, pp.2635–2654, 2008. 

   - [28] M. Balandat, B. Karrer, D.R. Jiang, S. Daulton, B. Letham, A.G. Wilson, and E. Bakshy, “BoTorch: A Framework for Efficient MonteCarlo Bayesian Optimization,” Advances in Neural Information Processing Systems 33, 2020. 

   - [29] J.R. Gardner, G. Pleiss, D. Bindel, K.Q. Weinberger, and A.G. Wilson, “Gpytorch: Blackbox matrix-matrix gaussian process inference with gpu acceleration,” Advances in Neural Information Processing Systems, 2018. 

   - [30] S. Ament, S. Daulton, D. Eriksson, M. Balandat, and E. Bakshy, “Unexpected improvements to expected improvement for bayesian optimization,” 2024. 

- [14] S. Zhang, W. Lyu, F. Yang, C. Yan, D. Zhou, X. Zeng, and X. Hu, “An efficient multi-fidelity bayesian optimization approach for analog circuit synthesis,” Proceedings of the 56th Annual Design Automation Conference 2019, DAC ’19, New York, USA, Association for Computing Machinery, 2019. 

- [15] R. Zhou, P. Poechmueller, and Y. Wang, “An analog circuit design and optimization system with rule-guided genetic algorithm,” IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems, vol.41, no.12, pp.5182–5192, 2022. 

- [16] Y. Yin, Y. Wang, B. Xu, and P. Li, “Ado-llm: Analog design bayesian optimization with in-context learning of large language models,” Proceedings of the 43rd IEEE/ACM International Conference on Computer-Aided Design, New York, USA, Association for Computing Machinery, 2025. 

- [17] D.V. Kochar, H. Wang, A. Chandrakasan, and X. Zhang, “Ledro: Llm-enhanced design space reduction and optimization for analog circuits,” 2025. 

- [18] Z. Huang, X. Li, Y. Li, K. Yue, H. Zeng, C. Cao, and Y. Chen, “Knowledge-aided automated synthesis for broadband power amplifier with transformer-coupled resonators,” IEEE Transactions on Circuits and Systems I: Regular Papers, vol.71, no.10, pp.4472–4485, 2024. 

- [19] A.F. Budak, P. Bhansali, B. Liu, N. Sun, D.Z. Pan, and C.V. Kashyap, “Dnn-opt: An rl inspired optimization for analog circuit sizing using deep neural networks,” 2021 58th ACM/IEEE Design Automation Conference (DAC), pp.1219–1224, 2021. 

- [20] Y. Choi, S. Park, M. Choi, K. Lee, and S. Kang, “Ma-opt: Reinforcement learning-based analog circuit optimization using multi-actors,” IEEE Transactions on Circuits and Systems I: Regular Papers, vol.71, no.5, pp.2045–2056, 2024. 

- [21] S. Zhang, F. Yang, C. Yan, D. Zhou, and X. Zeng, “An efficient batch-constrained bayesian optimization approach for analog circuit synthesis via multiobjective acquisition ensemble,” IEEE Transac- 

**Yuto Moriguchi** received his B.E. degree from Kyoto Institute of Technology, Kyoto, Japan, in 2024. His research interests include automated design of analog integrated circuits. He received the Best Paper Award from the Institute of Electrical Engineers of Japan in 2024. 



**Nobukazu Takai** received his B.E. and M.E. degrees from Tokyo University of Science, Tokyo, Japan, in 1993 and 1995, respectively, and the Doctor of Engineering degree from Tokyo Institute of Technology in 1999. He was with Tokyo Polytechnic University from 1999 to 2005, and with Gunma University from 2005 to 2022. Since 2022, he has been a Professor at Kyoto Institute of Technology. His main research interests lie in automatic analog integrated circuit design and the power supply circuitry of DC-DC converters. He received the Best Paper Award from the Institute of Electrical Engineers of Japan in 1999. Dr. Takai is a member of the Institute of Electronics, Information and Communication Engineers. 

