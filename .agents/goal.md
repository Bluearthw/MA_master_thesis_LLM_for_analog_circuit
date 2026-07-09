# Goal: Feedback-Driven Category-Level TD3 Transfer (`workflow_goal = 6`)

Use the `td3-llm-research-loop` skill for this goal.

Primary design source:

- `.agents/design.md`

Reference code inspected:

- `material/papers_found/codes_found/AutoSizer-main/llm_guided_ota_optimization_test.py`
- `material/papers_found/codes_found/AutoSizer-main/advanced_search_methods_test.py`
- `material/papers_found/codes_found/AutoSizer-main/utils/feedback_extraction.py`
- `material/papers_found/codes_found/Analogagent-main/agents.py`

## Overall Objective

Implement and evaluate the next version of `workflow_goal = 6`:

> Feedback-driven category-level TD3 transfer with optional LLM planning.

Normal TD3 remains the baseline. `workflow_goal = 6` should use evidence from previous circuits in the same category to configure TD3 for the next circuit before training starts. The LLM should act as a category-level planner or repair planner, not as the inner-loop sizing optimizer.

The research hypothesis is:

> Structured feedback from previous same-category TD3 runs can reduce average full-simulation cost by configuring warm-up, replay seeding, action constraints, low-fidelity use, and reward/spec weighting for later circuits, while preserving final strict-spec quality.

## Current V1 Baseline

Current `workflow_goal = 6` already has:

- OP/DC low-fidelity elite seeding;
- category-memory warm-start;
- reduced random warm-up;
- run summary logging;
- category-level adapter, validation, transfer-plan, and low-fidelity-policy helpers under `td3_llm_category_level/`.

Known V1 weakness:

- memory compatibility is still mostly exact YAML compatibility;
- fixed OP/DC seeding can add cost and make the workflow slower than baseline;
- category memory does not yet store enough TD3 trace feedback to guide the next circuit;
- reward/spec weighting and action-space decisions are not yet driven by previous run evidence;
- the current adapter is deterministic scaffolding, not a real LLM-planned category interface.

The next work should prioritize feedback collection and evidence-driven transfer before adding more LLM complexity.

## Research Boundary

The contribution should not be only:

> LLM narrows the search/action space.

That is close to AutoSizer.

The stronger contribution is:

> Previous same-category TD3 runs are converted into structured feedback, and an LLM-compatible transfer controller uses that feedback to configure later TD3 runs.

This differs from:

- AutoSizer: mostly per-circuit LLM search-space and optimizer orchestration;
- AnaFlow: mostly within-one-circuit reasoning and DC refinement;
- OP/DC-to-full BO work: low-to-high-fidelity transfer for BO, not category-level TD3 feedback transfer;
- GCN-RL/CAN/ADO-KT: topology/RL knowledge transfer without an LLM-compatible feedback planner;
- AnalogAgent: self-improvement inside an agent loop, not category-level RL trace transfer.

## Phase 0: Reconfirm Current State

### Deliverables

- Read `.agents/design.md`.
- Inspect `main.py`, `td3_runner.py`, `circuit_env.py`, `td3_llm/`, and `td3_llm_category_level/`.
- Identify the baseline TD3 path and the current `workflow_goal = 6` path.
- Confirm what feedback is currently saved after TD3 runs.

### Stop Condition

Stop Phase 0 when the current implementation state and missing feedback fields are summarized.

## Phase 1: TD3 Trace Collector

Add structured per-run feedback that can be reused by later circuits.

### Required Trace Fields

Save, at minimum:

- circuit id, category, run id, method name;
- parameter names, target names, observation dimension, action dimension;
- total wall time;
- full simulation count;
- low-fidelity simulation count;
- best reward progression;
- best candidate parameters;
- best measured metrics;
- strict pass/fail;
- failed specs and violation margins;
- top-k candidates;
- action distribution summary;
- boundary clustering for each parameter;
- repeated invalid/simulation-failure patterns;
- whether memory/replay/low-fidelity was used.

### Deliverables

- Add a durable JSON trace format under category memory or solutions.
- Keep it append-only.
- Do not change baseline TD3 behavior except for passive logging if needed.

### Stop Condition

Stop Phase 1 when a TD3 run or mocked run can produce a valid trace JSON without requiring a full long experiment.

## Phase 2: Feedback Analyzer

Convert traces into reusable transfer signals.

### Required Analyses

- convergence or stagnation detection;
- failed-spec ranking by normalized violation;
- parameter boundary clustering;
- top-k parameter pattern extraction;
- low-fidelity usefulness estimate;
- memory benefit or negative-transfer estimate;
- action groups that appear over-constrained;
- candidate regions to avoid.

### Deliverables

- Add deterministic analyzer code in `td3_llm_category_level/`.
- Produce a compact feedback summary JSON suitable for LLM input.
- Include actionable recommendations such as:
  - expand upper/lower bound;
  - narrow inactive range;
  - increase exploration for a parameter group;
  - reduce or skip OP/DC seeding;
  - reject harmful memory;
  - increase weight for a repeatedly failed spec.

### Stop Condition

Stop Phase 2 when existing or synthetic traces produce clear analyzer output.

## Phase 3: Category Transfer Planner

Use feedback summaries from previous circuits to configure the next circuit.

### Planner Inputs

- target circuit YAML and netlist;
- current deterministic adapter;
- feedback summaries from same category;
- category memory records;
- baseline/default TD3 settings.

### Planner Outputs

- selected memory records and rejection reasons;
- warm-start candidates;
- replay seed policy;
- low-fidelity policy: `skip`, `probe`, `gate`, or `pretrain`;
- action bounds/masks;
- exploration priority per parameter or action group;
- optional reward/spec weighting;
- fallback policy.

### Conservative Rule

The planner may narrow or bias TD3, but all restrictions must be reversible. If compatibility is weak, prefer logging the reason and falling back to baseline TD3.

### Stop Condition

Stop Phase 3 when the planner can explain transfer decisions for circuit `9` and at least one other circuit in the same category.

## Phase 4: TD3 Policy Applier

Apply the transfer plan to the actual TD3 runner.

### Allowed Controls

Start with controls that are cheap and reversible:

- warm-up length;
- replay seeding;
- low-fidelity mode;
- initial action noise scale;
- action bound overrides inside YAML limits;
- per-spec reward weights;
- early fallback if transferred probes underperform fresh probes.

Avoid actor/critic weight transfer until action/state/reward semantics are validated.

### Stop Condition

Stop Phase 4 when `workflow_goal = 6` can apply a transfer plan without changing normal TD3.

## Phase 5: Event-Triggered Repair Planner

Add repair only when evidence says transfer is hurting or training is stuck.

### Trigger Events

- repeated simulation failures;
- no reward improvement after a small budget;
- OP/DC gate rejects too many candidates;
- transferred candidates are worse than random probes;
- action bounds/masks block improvement;
- one spec repeatedly dominates failure.

### Allowed Repairs

- unfreeze action groups;
- expand bounds;
- drop incompatible memories;
- switch low-fidelity from `gate` or `pretrain` to `probe` or `skip`;
- increase exploration for selected groups;
- adjust reward weights for failed specs;
- fall back to baseline TD3.

### Stop Condition

Stop Phase 5 when a synthetic or real failure condition triggers a documented repair or fallback.

## Phase 6: Optional LLM Planner

Use the LLM only after deterministic feedback exists.

### LLM Role

The LLM may:

- summarize cross-circuit feedback;
- propose action-group priorities;
- explain why memories should transfer or be rejected;
- propose repair actions after stagnation;
- help map raw parameters to category roles.

The LLM must not:

- directly choose every TD3 action;
- silently relax final targets;
- output unvalidated parameter names, bounds, or specs into TD3.

### Validation

All LLM output must be checked by deterministic validators before it affects TD3.

### Stop Condition

Stop Phase 6 when an LLM-style planner output can be validated and either applied or rejected deterministically.

## Phase 7: Speed Trial

Run a controlled comparison against baseline TD3.

### Required Methods

Compare at least:

1. baseline TD3;
2. current `workflow_goal = 6`;
3. `workflow_goal = 6` with low-fidelity disabled;
4. `workflow_goal = 6` with category feedback transfer enabled.

Optional ablations:

- OP/DC seeding only;
- category memory only;
- feedback reward weighting only;
- feedback action-bound policy only.

### Required Circuits

- circuit `9`;
- at least one more circuit in category `1`.

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
- LLM call count and latency, if LLM is used;
- memory records used/rejected;
- fallback/repair events.

### Stop Condition

Stop Phase 7 when there is enough evidence to say whether the method is faster, slower, or inconclusive under the tested budget.

Do not claim speedup unless it is measured against baseline TD3 under comparable budgets.

## Phase 8: Paper/Thesis Positioning

Update the research notes after implementation/evaluation.

### Required Positioning

Clarify how this differs from:

- AnaFlow;
- AutoSizer;
- OP/DC-to-full BO work;
- GCN-RL/CAN/ADO-KT;
- PPAAS/RobustAnalog;
- AnalogAgent/LLM-USO memory.

### Stop Condition

Stop Phase 8 when the novelty boundary, failure modes, and next experiment are documented.

## Constraints

- Do not make destructive git changes.
- Commit only coherent changes; do not push.
- Preserve unrelated user changes in the working tree.
- If an architecture decision is ambiguous, choose the conservative option and document it.
- Put category-level logic in `td3_llm_category_level/`.
- Preserve normal TD3 as the baseline.
- Do not change production YAML targets unless the change is explicitly test-only and documented.
- Final strict-spec evaluation must use the original targets.
- Low-fidelity OP/DC must not be treated as final success.
- Do not let invalid LLM output affect TD3 before deterministic validation.
- Do not run a full RL/ngspice trial unless the user explicitly requests it or the current phase requires it.

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
