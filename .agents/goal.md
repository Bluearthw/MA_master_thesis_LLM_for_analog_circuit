# Goal: Design-Driven `workflow_goal = 6` LLM-RL Sizer

Use the `td3-llm-research-loop` skill for this goal.

Primary design source:

- `.agents/design.md`

## Overall Objective

Implement and evaluate the next version of `workflow_goal = 6`:

> LLM-validated category transfer for TD3.

Normal TD3 remains the baseline. The LLM should shape the RL problem through validated adapters, transfer plans, memory compatibility, action grouping, and adaptive low-fidelity policy. The LLM should not directly choose every next sizing vector.

The research hypothesis is:

> LLM-extracted and deterministically validated category knowledge can reduce average TD3 sizing cost across circuits in one category without reducing final strict-spec quality.

## Current V1 Baseline

Current `workflow_goal = 6` already has:

- OP/DC low-fidelity elite seeding;
- category-memory warm-start;
- reduced random warm-up;
- run summary logging.

Known V1 weakness:

- memory compatibility is too strict because it requires exact YAML parameter/target compatibility;
- fixed OP/DC seeding can add cost and make the workflow slower than baseline;
- there is not yet a real LLM adapter for role/action mapping across topology variants.

The next work should fix these weaknesses rather than only running more V1 trials.

## Phase 0: Reconfirm Baseline and Design State

### Deliverables

- Read `.agents/design.md`.
- Inspect the current `workflow_goal = 6`, `td3_runner.py`, `td3_llm/`, and `circuit_env.py`.
- Identify what already exists and what is missing.
- Do not modify code in this phase unless a trivial broken import blocks inspection.

### Stop Condition

Stop Phase 0 when the current implementation state is summarized in the working notes or final report.

## Phase 1: LLM Circuit Adapter Schema

Implement a structured adapter interface. The adapter is the bridge between circuit-specific YAML/netlist/contracts and category-level RL memory.

### Required Adapter Fields

The adapter should be JSON-serializable and include:

- category;
- topology subtype;
- device roles;
- matched groups;
- action groups;
- initial action mask;
- parameter-bound overrides;
- DC/OP feasibility terms;
- spec-to-action hints;
- memory retrieval keys;
- confidence and evidence.

### Deliverables

- Add a schema/model or plain validation-friendly dictionary structure.
- Add a deterministic sample adapter for at least circuit `9`.
- Save adapter artifacts under a durable experiment or memory directory.
- Keep baseline TD3 unchanged.

### Stop Condition

Stop Phase 1 when an adapter can be created, serialized, loaded, and inspected for circuit `9` without running a full RL experiment.

## Phase 2: Deterministic Adapter Validator

Build a non-LLM validator before adapters can affect TD3.

### Required Checks

- referenced device/parameter names exist;
- matched groups are structurally plausible;
- action groups map to legal YAML parameters;
- target/spec names exist and preserve YAML target order;
- parameter bounds remain inside YAML/technology limits;
- required simulation outputs are available;
- action masks are reversible and cannot permanently remove every variable affecting a hard constraint.

### Deliverables

- Add validator code and validation result logging.
- Reject invalid adapters with actionable error messages.
- Fall back to V1 warm-start or plain TD3 when validation fails.

### Stop Condition

Stop Phase 2 when valid and intentionally invalid adapter examples produce correct validation results.

## Phase 3: Transfer Planner

Implement transfer planning using the validated adapter and category memory.

### Transfer Options

Support transfer decisions in this order, from safest to riskiest:

1. successful candidate points;
2. OP/DC-feasible candidate points;
3. failure patterns and invalid regions;
4. action bounds and grouped actions;
5. replay transitions transformed into canonical role/action coordinates;
6. actor/critic weights only when dimensions and semantics match.

### Required Plan Fields

The transfer plan should include:

- memory records used;
- memory records rejected and why;
- warm-start candidates;
- replay seed policy;
- weight transfer policy;
- low-fidelity policy: `skip`, `probe`, `gate`, or `pretrain`;
- fallback policy.

### Stop Condition

Stop Phase 3 when the planner can explain why it uses or rejects existing category memory for at least circuits `9` and one other circuit in the same category.

## Phase 4: Adaptive Low-Fidelity Policy

Replace fixed low-fidelity cost with an adaptive policy.

### Policy Modes

- `skip`: no low-fidelity calls;
- `probe`: run a few OP/DC checks to estimate usefulness;
- `gate`: OP/DC must pass before expensive full simulation;
- `pretrain`: use OP/DC feasibility for early seeding/pretraining.

### Decision Metrics

Track:

- OP/DC pass rate;
- full-spec reward of OP/DC elites;
- correlation between OP/DC reward and full-spec reward;
- full simulation failures avoided;
- wall-clock cost saved or added.

### Stop Condition

Stop Phase 4 when `workflow_goal = 6` can choose `skip`, `probe`, `gate`, or `pretrain` from measurable evidence rather than hardcoding OP/DC seeding every time.

## Phase 5: Canonical Category Interface

Make category-level transfer possible even when YAML parameter names and action dimensions differ.

### Initial Scope

Start with one category, preferably category `1` if that is the current amplifier/simple analog category.

### Canonical Action Groups

Use adapter-derived roles such as:

- input pair width;
- input pair length;
- load/mirror width;
- load/mirror length;
- tail bias/current;
- cascode bias;
- compensation capacitor;
- output device size;
- bias voltage/current source;
- load/passive element.

### Deliverables

- Map raw YAML params to canonical action groups.
- Allow missing roles through masks.
- Map canonical TD3 actions back to circuit-specific params.
- Save mapping evidence in category memory.

### Stop Condition

Stop Phase 5 when two circuits in the same category can be represented in the same canonical interface, even if their raw YAML params differ.

## Phase 6: RL Monitor and Repair Agent

Add event-triggered monitoring and repair.

### Trigger Events

- repeated simulation failures;
- no reward improvement after a small budget;
- OP/DC gate rejects too many candidates;
- transferred memory performs worse than fresh random probes;
- action mask appears to block improvement.

### Allowed Repairs

- unfreeze action groups;
- expand bounds;
- reject incompatible memories;
- switch low-fidelity mode from `gate`/`pretrain` to `probe`/`skip`;
- add missing diagnostic features;
- fall back to baseline TD3.

### Stop Condition

Stop Phase 6 when at least one synthetic or real failure condition triggers a documented repair or fallback.

## Phase 7: Speed and Quality Evaluation

Run a controlled comparison against baseline TD3.

### Required Methods

Compare:

1. baseline TD3;
2. TD3 with equal reduced warm-up;
3. OP/DC seeding only;
4. category memory only;
5. LLM action grouping only;
6. LLM adapter + memory + transfer gate;
7. same as 6 but low-fidelity disabled.

### Metrics

Report:

- wall-clock time;
- full simulation count;
- low-fidelity simulation count;
- total simulator calls;
- success rate;
- best reward;
- final strict-spec pass/fail;
- first feasible step, if available;
- LLM call count and latency;
- memory records used/rejected;
- fallback/repair events.

### Stop Condition

Stop Phase 7 when there is enough evidence to say whether the design is faster, slower, or inconclusive under the tested budget.

Do not claim speedup unless it is measured against baseline TD3 under comparable budgets.

## Phase 8: Paper/Thesis Positioning

Update the research notes after implementation/evaluation.

### Required Positioning

Clarify how this differs from:

- AnaFlow;
- AutoSizer;
- OP/DC-to-full BO work;
- GCN-RL/CAN;
- PPAAS/RobustAnalog;
- AnalogAgent/LLM-USO memory.

### Stop Condition

Stop Phase 8 when the novelty boundary, failure modes, and next experiment are documented.

## Constraints

- Do not make destructive git changes.
- Commit only coherent changes; do not push.
- Preserve unrelated user changes in the working tree.
- If an architecture decision is ambiguous, choose the conservative option and document it.
- Do not change production YAML targets unless the change is explicitly test-only and documented.
- Final strict-spec evaluation must use the original targets.
- Low-fidelity OP/DC must not be treated as final success.
- Do not let invalid LLM output affect TD3 before deterministic validation.

## Final Report Requirements

Every run must report:

- phases completed;
- files changed;
- commands run;
- tests passed/failed;
- whether full RL/ngspice runs were performed;
- baseline comparison status;
- commit hash if committed;
- remaining risks;
- next recommended phase.

