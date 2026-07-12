# Design 2: Category-Level DC Setter and Curated Sizing Guide

Status: research design proposal; no implementation yet

## Objective

Use an LLM-based DC Setter to produce simulation-grounded warm-start candidates for TD3, then distill the completed sizing trajectory into a role-based category guide that can help size later circuits of the same type.

The first circuit may cost more than baseline because it creates knowledge. The research hypothesis is that average simulation cost decreases across a sequence of circuits in the same category.

## Research Position

For one circuit, the DC Setter resembles AnaFlow:

```text
circuit understanding
        -> initial DC sizing proposal
        -> OP/DC simulation
        -> feedback-driven parameter revision
        -> validated candidates seed TD3
```

The category-level contribution begins after this loop:

```text
DC Setter trajectory + OP/DC evidence + full-spec outcome
        -> Category Curator
        -> role-based sizing guide
        -> circuit-specific Adapter
        -> DC Setter for the next circuit
```

Unlike AnaFlow's within-circuit memory, the proposed workflow stores reusable lessons across heterogeneous circuits in one category. Unlike blind replay transfer, it maps lessons through semantic device roles and validates them against each new circuit.

## Runtime Scope

This design belongs to:

```text
workflow_goal = 2
mode = category_llm_rl
```

Baseline TD3 remains unchanged.

## Phase A: Circuit Understanding

Before calling the DC Setter, construct a deterministic circuit context containing:

- circuit ID and category;
- netlist;
- YAML parameter names, bounds, steps, and units;
- YAML targets and min/max directions;
- matching and symmetry constraints;
- available OP/DC measurements;
- validated topology and device-role mapping;
- relevant lessons retrieved from the category guide.

The LLM may explain topology, but deterministic validation must reject references to nonexistent devices, parameters, targets, or measurements.

## Phase B: DC Setter

The DC Setter must use `get_client()` and `call_agent()` from `utils/agent_utils.py`. It is an actual LLM agent with a structured response schema, not a pure Python heuristic.

### Input Contract

```json
{
  "circuit_id": "9",
  "category": "amplifier",
  "topology_summary": {},
  "device_roles": {},
  "parameters": [
    {
      "name": "W_M1",
      "role": "input_differential_pair.width",
      "minimum": 1e-6,
      "maximum": 100e-6,
      "step": 1e-6,
      "unit": "m"
    }
  ],
  "matching_constraints": [],
  "dc_requirements": {},
  "full_targets_context": {},
  "category_lessons": [],
  "previous_iteration_feedback": [],
  "candidate_count": 8
}
```

DC requirements are primary. Full targets are context only: the DC Setter must not claim that OP analysis predicts AC, noise, transient, or other unavailable measurements.

### Output Contract

```json
{
  "analysis_summary": "Bias the input pair at moderate inversion while preserving headroom.",
  "applied_lesson_ids": [],
  "candidates": [
    {
      "candidate_id": "dc_001",
      "parameters": {},
      "intent": "balanced moderate-current input pair",
      "expected_dc_effects": [
        {
          "metric": "input_pair_gm",
          "direction": "increase"
        }
      ],
      "confidence": 0.72
    }
  ]
}
```

The agent returns physical parameter values. Deterministic code owns conversion to normalized TD3 actions.

### Deterministic Validation

Before simulation:

1. Reject unknown, missing, duplicate, nonfinite, or nonnumeric values.
2. Reject or clamp values outside YAML bounds according to an explicit policy.
3. Quantize values to YAML steps.
4. Enforce matching and tied-parameter constraints.
5. Convert validated parameter values to TD3 actions in `[-1, 1]`.
6. Reject candidates that collapse to duplicates after quantization.

The LLM must not generate rewards, simulated specifications, replay states, or pass/fail claims. Those fields belong to deterministic simulation and evaluation.

## Phase C: Feedback-Driven DC Loop

Each accepted candidate receives an OP/DC simulation. The next DC Setter call receives compact feedback:

- proposed and realized parameter values;
- OP/DC measurements;
- operating-region and headroom failures;
- deterministic low-fidelity reward components;
- parameter changes from the previous iteration;
- whether each measured quantity improved or regressed;
- remaining DC problems.

Stop the loop when one of these conditions is met:

- enough DC-feasible candidates exist;
- no meaningful improvement occurs for a fixed number of iterations;
- the LLM-call or OP/DC budget is reached;
- repeated invalid outputs trigger fallback.

Selected DC candidates receive full-spec simulation and seed TD3 replay using the existing warm-start record format.

## Sobol Safety Net

Do not remove Sobol in the first implementation. Compare or combine it with the DC Setter:

```text
LLM topology-aware candidates
        +
Sobol space-filling candidates
        -> same OP/DC evaluator
        -> common ranking
        -> full-spec elites
        -> TD3 replay
```

Candidate-source labels must be preserved so the experiment can measure whether LLM, Sobol, or the combination produced useful full-spec seeds.

## Phase D: Category Curator

The Curator runs after a circuit completes or reaches a meaningful milestone, not after every simulation. It uses another structured `call_agent()` call.

### Curator Input

- validated topology and role mapping;
- full DC Setter proposal/feedback trajectory;
- accepted and rejected candidates;
- deterministic OP/DC measurements and reward components;
- full-spec results of selected candidates;
- final TD3 outcome;
- parameter sensitivity summaries calculated by Python;
- current category guide.

### Curator Output

```json
{
  "category": "amplifier",
  "lessons": [
    {
      "lesson_id": "amp_dc_001",
      "condition": "input pair has insufficient gm with available headroom",
      "action": {
        "role": "input_differential_pair",
        "parameter": "width",
        "direction": "increase",
        "magnitude": "small"
      },
      "expected_effects": {
        "gm": "increase",
        "input_noise": "may decrease",
        "bias_current": "may increase"
      },
      "applicability": {},
      "evidence_ids": [],
      "evidence_count": 3,
      "confidence": 0.78
    }
  ],
  "failed_heuristics": [],
  "open_questions": []
}
```

Every lesson must cite stored simulation evidence. A single LLM explanation without measured support remains a hypothesis, not a reusable rule.

## Transferable Knowledge

### Directional Knowledge

- which functional role and parameter should change for a specific DC condition;
- expected direction of effects and likely trade-offs;
- effective normalized change magnitude.

### Constraint Knowledge

- matching groups and tied controls;
- saturation, headroom, and bias relationships;
- combinations and normalized regions associated with repeated failure.

### Search Knowledge

- sensitive role groups;
- productive normalized parameter regions;
- useful DC termination conditions;
- whether DC quality correlated with full-spec quality;
- whether Sobol, LLM, or mixed candidate generation worked best.

### Knowledge Not Transferred Blindly

- raw transistor names such as `M1`;
- raw action indices;
- absolute widths or lengths across incompatible circuits or processes;
- replay transitions with different action or observation semantics;
- critic or actor weights without compatibility checks;
- a DC improvement contradicted by full-spec measurements.

## Phase E: New-Circuit Adapter

For the next circuit, an Adapter maps category roles to local parameters:

```text
category lesson:
input_differential_pair.width increase
        -> topology/device-role mapping
        -> local parameters W_M3 and W_M4
        -> matching constraint W_M3 == W_M4
```

The Adapter must label each lesson as:

- `applicable`;
- `partially_applicable`;
- `incompatible`;
- `uncertain`.

Only applicable, deterministically valid lessons enter the DC Setter prompt. Uncertain lessons may be tested with a small probe but cannot narrow the action space permanently.

## Memory Layout

Use append-only durable records under `solutions/category_memory/`:

```text
solutions/category_memory/<category>/
    circuits/<circuit_id>/dc_trajectory.json
    circuits/<circuit_id>/curator_input.json
    circuits/<circuit_id>/curator_output.json
    guides/category_dc_guide.json
    evidence/evidence_index.json
```

Each lesson stores circuit IDs, run IDs, evidence IDs, topology applicability, model metadata, creation time, and validation status.

## Fallbacks

- Invalid DC Setter response: retry within the existing `call_agent()` policy, then use Sobol.
- No DC improvement: stop the LLM loop and continue with Sobol or baseline TD3.
- Invalid category mapping: ignore transferred lessons for that circuit.
- Negative transfer: remove transferred candidates and action guidance, then continue fresh.
- LLM unavailable: preserve a fully deterministic Sobol + TD3 path.

## Experimental Evaluation

Run circuits in a fixed sequence within one category and compare equal budgets:

1. baseline TD3 with random full-spec warm-up;
2. Sobol OP/DC warm-start + TD3;
3. per-circuit DC Setter + TD3, without category memory;
4. category Curator guide + DC Setter + TD3;
5. category Curator guide + DC Setter + Sobol + TD3.

Report per circuit and category average:

- OP/DC simulations;
- full-spec simulations;
- first strict-pass simulation count;
- strict success rate;
- best reward under a fixed budget;
- wall time;
- number and time of LLM calls;
- invalid agent outputs;
- accepted/rejected transferred lessons;
- positive and negative transfer rate.

The main claim is supported only if category transfer improves later circuits enough to offset the first circuit's knowledge-creation cost.

## Minimal Implementation Order

1. Implement the DC Setter schema, prompt, validator, and metrics without category memory.
2. Compare DC Setter candidates against Sobol under equal OP/DC and full-spec budgets.
3. Save deterministic trajectories and evidence.
4. Add the Curator and append-only category guide.
5. Add the new-circuit Adapter and applicability validation.
6. Run the fixed-sequence category-level ablation.

This order isolates whether the DC Setter itself helps before attributing improvements to category-level transfer.
