# Design: Category-Level LLM-Assisted RL Sizer (`workflow_goal = 6`)

Status: design proposal for the next version of `workflow_goal = 6`

## Decision

`workflow_goal = 6` should keep low-fidelity simulation, but it should not use low-fidelity as a fixed extra stage for every run.

Low-fidelity OP/DC analysis should be an adaptive tool used by the LLM-RL controller to answer specific questions:

- Is this candidate even electrically alive?
- Are important devices biased in plausible operating regions?
- Is the transferred memory compatible with this new circuit?
- Should TD3 run full-spec simulation for this candidate, or reject/repair first?
- Has a narrowed action space trapped the search in a bad region?

The Phase 2 pilot showed that fixed OP/DC seeding can make `workflow_goal = 6` slower than baseline because it adds low-fidelity simulations before full simulations. Therefore, the next design should treat low-fidelity as a gate and diagnostic signal, not as mandatory overhead.

## Intended Research Claim

The target claim is not:

> LLM narrows action space.

That is already close to AutoSizer and related work.

The stronger claim is:

> An LLM-generated and deterministically validated circuit adapter enables category-level TD3 transfer by mapping different circuits into reusable roles, action groups, feasibility checks, simulation schedules, and memory compatibility rules.

This makes `workflow_goal = 6` different from:

- AnaFlow: mostly within-one-circuit reasoning and DC refinement;
- AutoSizer: per-circuit LLM search-space/optimizer orchestration;
- OP/DC-to-full BO papers: low-to-high fidelity scheduling for BO;
- GCN-RL/CAN: topology-aware RL transfer without an LLM contract adapter.

## High-Level Architecture

```text
new circuit + YAML + contracts + previous category memory
        |
        v
LLM Circuit Adapter Agent
        |
        v
Deterministic Adapter Validator
        |
        v
Transfer Planner Agent
        |
        +--> action groups / masks / bounds
        +--> compatible memory retrieval
        +--> OP/DC gate policy
        +--> TD3 warm-start / replay seeding plan
        |
        v
TD3 RL Sizer
        |
        v
RL Monitor and Repair Agent
        |
        v
Category Memory Curator
```

The LLM should shape the RL problem. It should not directly choose every next sizing vector.

## Agent Roles

### 1. Circuit Adapter Agent

Runs once before sizing unless validation fails or TD3 stagnates.

Inputs:

- netlist;
- YAML params and targets;
- simulation contracts;
- category description;
- optional previous category memories.

Outputs a structured JSON adapter:

```json
{
  "category": "amplifier",
  "topology_subtype": "common_source_or_ota_or_unknown",
  "device_roles": {},
  "matched_groups": [],
  "action_groups": [],
  "initial_action_mask": [],
  "parameter_bounds_overrides": {},
  "dc_feasibility_terms": [],
  "spec_to_action_hints": [],
  "memory_retrieval_keys": [],
  "confidence": {},
  "evidence": {}
}
```

Required behavior:

- prefer uncertainty over hallucinated precision;
- mark unsupported topology parts explicitly;
- explain every role/action group with netlist evidence.

### 2. Deterministic Adapter Validator

This is not an LLM.

It checks:

- all referenced device/parameter names exist;
- matched groups are structurally plausible;
- action groups map to legal YAML parameters;
- target/spec names exist and preserve YAML target order;
- parameter bounds are within technology/YAML limits;
- required simulation outputs are available;
- no fixed action mask can permanently remove all variables affecting a hard constraint.

If validation fails, fall back to:

```text
plain TD3 or V1 category-memory warm-start
```

### 3. Transfer Planner Agent

Uses the validated adapter and category memory to decide what can transfer.

Transfer options, from safest to riskiest:

1. successful candidate points;
2. OP/DC-feasible candidate points;
3. failure patterns and invalid regions;
4. action bounds and grouped actions;
5. replay transitions transformed into canonical role coordinates;
6. actor/critic weights only when dimensions and semantics match.

The planner should output a transfer plan:

```json
{
  "memory_records_used": [],
  "memory_records_rejected": [],
  "warm_start_candidates": [],
  "replay_seed_policy": "none|points_only|compatible_transitions",
  "weight_transfer_policy": "none|actor_only|actor_and_critic",
  "low_fidelity_policy": "skip|probe|gate|pretrain",
  "fallback_policy": {}
}
```

### 4. TD3 RL Sizer

TD3 remains the numerical optimizer.

Inputs from the LLM/adapter:

- reduced or grouped action interface;
- candidate seeds;
- replay seeds;
- action-noise bias or exploration priority;
- OP/DC gate rules;
- normalized reward terms from contracts.

The final reward and strict pass/fail must remain deterministic.

### 5. RL Monitor and Repair Agent

Runs only on events:

- repeated simulation failures;
- no reward improvement after a small budget;
- OP/DC gate rejects too many candidates;
- critic uncertainty/reward slope suggests action mask is blocking progress;
- transferred memory performs worse than fresh random probes.

Allowed repairs:

- unfreeze action groups;
- expand bounds;
- reject incompatible memories;
- change low-fidelity policy from `gate` to `skip`;
- add missing state/reward diagnostic features;
- fall back to baseline TD3.

Not allowed:

- silently relax final targets;
- overwrite original YAML targets;
- invent device names or measurements.

### 6. Category Memory Curator

After every run, save both successful and failed evidence.

Memory should include:

- circuit id and category;
- topology subtype;
- validated adapter;
- YAML params/targets signatures;
- action groups and role mappings;
- best candidates;
- OP/DC metrics;
- full-spec metrics;
- replay summary statistics;
- failure patterns;
- whether transfer helped or hurt.

Memory should be append-only unless a deterministic cleanup step is explicitly run.

## What Knowledge Can Transfer Between Circuits?

### Transferable LLM-Side Knowledge

- device roles: input pair, current mirror, tail source, load, cascode, bias, compensation, output stage;
- matched/tied parameter groups;
- topology subtype and functional blocks;
- likely high-impact variables;
- spec-to-action influence hints;
- safe initial parameter ranges;
- OP/DC feasibility rules;
- common simulation failure patterns;
- action-mask repair rules;
- compatibility explanations for old memories.

### Transferable RL-Side Knowledge

- successful normalized candidate points when parameter semantics match;
- OP/DC-feasible points;
- replay transitions in a canonical role/action coordinate system;
- actor weights only for compatible action/state semantics;
- critic weights only when reward semantics and observation layout match;
- exploration priors for action groups;
- negative-transfer statistics.

### Knowledge That Should Not Transfer Blindly

- raw transistor names;
- raw action indices;
- exact widths/lengths across different technologies or topology variants;
- replay buffers without coordinate transformation;
- critic values across different reward definitions;
- OP/DC reward as if it were full-spec reward;
- masks that cannot be reversed.

## Low-Fidelity Policy

Low-fidelity is useful, but only if it reduces wasted full simulations.

Use four modes:

| Mode | Meaning | When to use |
|---|---|---|
| `skip` | no low-fidelity calls | strong compatible memory exists or OP/DC was unhelpful |
| `probe` | run a few OP/DC checks to estimate correlation | new topology or uncertain adapter |
| `gate` | OP/DC must pass before expensive full simulation | many candidates fail due to bias/convergence |
| `pretrain` | train/seed TD3 from OP/DC feasibility first | first circuit in a category or no useful memory |

Recommended default:

```text
first circuit in category: probe -> maybe pretrain
later compatible circuit: probe -> gate only if useful
strong negative transfer: skip low-fidelity and use baseline TD3
```

The controller should estimate whether low-fidelity is helping:

- OP/DC pass rate;
- full-spec reward of OP/DC elites;
- correlation between OP/DC reward and full-spec reward;
- full simulation failures avoided;
- wall-clock cost saved.

If low-fidelity adds cost without improving full-spec reward or avoiding failures, turn it off for that topology/memory cluster.

## Canonical Category Interface

The current V1 memory requires exact YAML compatibility. That is too strict for real category-level transfer.

V2 should introduce a canonical category interface:

```text
raw YAML params
        |
        v
LLM role/action adapter
        |
        v
canonical action groups
        |
        v
TD3 policy/replay/memory
        |
        v
adapter maps actions back to circuit-specific params
```

Example canonical amplifier action groups:

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

For circuits without a given role, that slot is masked but represented in the adapter metadata.

## Reward Design

Use separate stage rewards.

### OP/DC Feasibility Reward

Used only for ranking, gating, or pretraining:

```text
R_op =
  saturation/headroom score
+ alive-device score
+ output/common-mode sanity
+ current sanity
+ convergence score
- parser/simulation failure penalty
```

### Full-Spec Reward

Used for final TD3 training and evaluation:

```text
R_full =
  normalized hard-constraint satisfaction
+ clipped soft-objective score
+ all-spec-pass bonus
- invalid simulation penalty
```

Do not train one critic on mixed OP and full rewards unless the state includes a fidelity token and missing-metric mask.

## Suggested `workflow_goal = 6` Runtime

```text
1. Load circuit/category/contracts/YAML.
2. Retrieve category memory summaries.
3. Call LLM Circuit Adapter Agent.
4. Validate adapter deterministically.
5. Select transfer plan:
   - memory candidates;
   - action groups/masks;
   - low-fidelity mode;
   - TD3 budget.
6. Run small transfer probe:
   - fresh random probes;
   - transferred probes;
   - optional OP/DC probes.
7. If transfer helps, continue with transferred TD3.
8. If transfer hurts, drop replay/masks and fall back.
9. Save all evidence to category memory.
```

## Minimum Ablations

To show the mechanism is real, compare:

1. baseline TD3;
2. TD3 with equal reduced warm-up;
3. OP/DC seeding only;
4. category memory only;
5. LLM action grouping only;
6. LLM adapter + memory + transfer gate;
7. same as 6 but low-fidelity disabled.

The low-fidelity-disabled ablation is important. It answers whether OP/DC is helping or just adding cost.

## Answer to the Design Question

Should `workflow_goal = 6` have low-fidelity things?

Yes, but only as an adaptive sub-tool. It should not be the main identity of the workflow and should not be paid on every circuit by default.

The main identity of `workflow_goal = 6` should be:

> LLM-validated category transfer for TD3.

Low-fidelity OP/DC analysis supports that identity by testing feasibility, validating transferred knowledge, and avoiding wasted full simulations. If it does not reduce full simulations or improve reward, the controller should disable it for that circuit/topology cluster.

