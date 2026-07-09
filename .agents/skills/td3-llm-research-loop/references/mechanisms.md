# Mechanism Reference

Use this file only when selecting or justifying a TD3/LLM research mechanism.

## Preferred Mechanism Order

1. Category-memory warm-start.
   - Save successful/high-reward candidate params, specs, reward, circuit, category, target signature, and action dimensions.
   - Retrieve only compatible records.
   - Convert params to normalized actions and evaluate in the new environment before seeding replay.

2. LLM adapter for action structure.
   - Extract device roles, matched groups, likely high-impact variables, and safe ranges.
   - Validate against netlist/YAML/contracts.
   - Use reversible masks; expand when stagnation or sensitivity evidence shows the mask is blocking progress.

3. DC/OP feasibility stage.
   - Use cheap checks for convergence, saturation/headroom, current sanity, output common-mode, and parser failures.
   - Treat this as pretraining, ranking, or warm-start, not final success.

4. Transfer gate.
   - Probe transferred and fresh starts under a small budget.
   - Continue transfer only if feasibility rate, reward slope, or full-spec probe reward improves.
   - Drop replay first, then reset heads/weights if negative transfer appears.

5. Relaxed-target curriculum.
   - Use relaxed specs only to make early rewards smoother.
   - Verify final candidates with strict original targets.

## Knowledge the LLM May Transfer

- device roles;
- matched/tied action groups;
- topology subtype;
- likely high-impact parameters;
- spec-to-device influence hints;
- DC/OP feasibility rules;
- simulation failure patterns;
- compatibility explanation for retrieved memories.

## Knowledge the LLM Must Not Assume

- same device names across circuits;
- same parameter count or action dimension;
- same topology inside one category;
- same target ordering;
- same reward semantics across DC-only and full-spec stages.

## Prior-Art Boundaries

- OP/DC-to-full simulation staging exists in BO-style work.
- LLM action-space narrowing exists in AutoSizer/TopoSizing-like work.
- LLM memory exists in AnalogAgent/LLM-USO-like work.
- Transferable topology-aware RL exists in GCN-RL/CAN-like work.

The safer claim is: LLM-extracted, validated category knowledge controls how TD3 reuses action structure, replay, warm-start candidates, and DC-stage knowledge across circuits while preserving fallback to baseline TD3.
