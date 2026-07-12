# Goal: Minimal LLM DC Setter

## Objective

Create a simple LLM DC Setter that proposes initial parameter candidates for DC-gain warm-up before TD3 sizing. The setter prioritizes DC-bias parameters, but DC gain is measured using AC analysis.

The agent must use `get_client()` and `call_agent()` from `utils/agent_utils.py`. It must not be implemented as a pure Python sizing heuristic.

## Initial Scope

Start with the minimum legal value of every parameter. The DC Setter should then:

1. Change DC-bias controls first, such as bias current, bias voltage, multiplicity, or other parameters that directly establish the operating point.
2. Preserve the minimum W/L values when bias changes are sufficient.
3. Change W/L only when bias controls cannot establish a useful operating point or strong category knowledge requires it, such as a PMOS normally needing greater width than a comparable NMOS.
4. Keep every proposed value within the provided parameter bounds.
5. Generate multiple candidates in one LLM call.

Units are not included in the contract. Category-specific sizing guidance belongs in the prompt or retrieved experience.

## Agent Input

Provide only:

```json
{
  "category": "amplifier",
  "netlist": "...",
  "experience": [],
  "parameters": {
    "W_M1": {
      "minimum": 1e-6,
      "maximum": 100e-6,
      "step": 1e-6
    }
  }
}
```

Python selects relevant lesson IDs by scanning category memory before building `experience`. The LLM does not select or return lesson IDs.

## Agent Output

```json
{
  "analysis_summary": "Adjust the bias controls first and retain minimum device sizes where possible.",
  "candidates": [
    {
      "candidate_id": "dc_gain_1",
      "parameters": {
        "W_M1": 1e-6
      },
      "increase_dc_gain": true
    },
    {
      "candidate_id": "dc_gain_2",
      "parameters": {
        "W_M1": 2e-6
      },
      "increase_dc_gain": false
    }
  ]
}
```

`increase_dc_gain` is the LLM's expected direction, not a measured result. Python must determine the actual low-frequency gain through AC simulation.

Candidate IDs use the deterministic format `dc_gain_<index>`. Python should assign or overwrite these IDs to prevent malformed or duplicate identifiers.

## Python Responsibilities

- Build the minimum-size baseline candidate.
- Retrieve relevant category experiences and retain their lesson IDs outside the agent response.
- Validate parameter names, completeness, finite values, bounds, and steps.
- Enforce any known matching constraints outside the LLM.
- Quantize parameter values when digitized mode is enabled.
- Convert physical parameter dictionaries into normalized TD3 actions.
- Reject duplicate candidates after validation and quantization.
- Run OP analysis first to reject candidates with invalid bias, operating regions, or headroom.
- Run AC analysis for OP-feasible candidates to measure low-frequency DC gain.
- Calculate the deterministic warm-start reward from OP feasibility and measured AC gain.
- Record the candidate source, selected lesson IDs, LLM-call metrics, and simulation result.
- Fall back to Sobol warm-up if the LLM call or validation fails.

## Stop Condition

Stop this goal when:

- the DC Setter produces schema-valid candidate parameter lists;
- candidates pass deterministic validation and can be converted into TD3 actions;
- at least one focused mocked or reduced-cost test verifies the path;
- no full RL run is required unless explicitly requested.

## Non-Goals

- No category Curator implementation yet.
- No full-spec reasoning beyond DC gain.
- No direct LLM-generated rewards or pass/fail decisions.
- No replacement of baseline TD3 or Sobol.
- No transfer of actor or critic weights.

## Constraints

- Do not make destructive git changes.
- Commit only coherent changes; do not push.
- Preserve unrelated user changes in the working tree.
- If an architecture decision is ambiguous, choose the conservative option and document it.
- Put category-level logic in `td3_llm_category_level/`.
- Preserve normal TD3 as the baseline.
- Do not change production YAML targets unless the change is explicitly test-only and documented.
- Final strict-spec evaluation must use the original targets.
- Low-fidelity OP/AC warm-start results must not be treated as final strict-spec success.
- Do not let invalid LLM output affect TD3 before deterministic validation.
- Do not run a full RL/ngspice trial unless the user explicitly requests it or the current phase requires it.
