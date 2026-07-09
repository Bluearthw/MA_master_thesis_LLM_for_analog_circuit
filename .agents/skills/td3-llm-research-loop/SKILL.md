---
name: td3-llm-research-loop
description: Goal-driven research workflow for analog IC sizing projects that improve TD3/RL with LLM or category-level knowledge. Use when the user asks Codex to read a goal file, iterate on an LLM-assisted TD3 sizer, add a new workflow_goal, compare against baseline TD3, diagnose failed sizing experiments, or consult analog sizing papers/materials after implementation or test failure.
---

# TD3 LLM Research Loop

## Purpose

Use this skill to run a disciplined research loop for analog circuit sizing work where normal TD3 is the baseline and new LLM/RL mechanisms are experimental. Optimize for small measurable changes, explicit validation, and conservative fallback.

## Core Loop

1. Read the current goal.
   - Prefer `.agents/goal.md` when present.
   - Fall back to `material/codex_night/goal.md` only for older threads.
   - Extract deliverable, target workflow goal number, circuit/category, stop condition, constraints, and allowed test depth.
   - If the user pasted a newer goal, use the pasted text over stale file context.

2. Map the current implementation.
   - Inspect `main.py`, `td3_runner.py`, `circuit_env.py`, `td3/`, `td3_llm/`, `td3_llm_category_level/`, YAML target paths, and existing workflow routing as needed.
   - Identify the baseline path before changing anything.
   - Preserve baseline TD3 behavior unless the goal explicitly requests baseline changes.

3. Propose the smallest mechanism.
   - State a 3-6 bullet implementation plan before edits.
   - Prefer default-off mechanisms first: category memory, replay warm-start, action grouping, DC/OP feasibility pre-screen, transfer gate, or relaxed-target curriculum with strict final evaluation.
   - Read `references/mechanisms.md` when choosing or justifying the mechanism.

4. Implement narrowly.
   - Add a new `workflow_goal` path rather than altering existing workflows when possible.
   - Keep production YAML targets unchanged unless the user explicitly asks for test-only changes.
   - Use deterministic validation for LLM outputs before they affect RL.
   - Make fallback to plain TD3 explicit when adapter/memory compatibility fails.

5. Validate with the cheapest meaningful tests.
   - Run `venv\Scripts\python.exe -m py_compile` on changed Python modules.
   - Prefer helper tests and smoke tests over full ngspice/RL runs.
   - Run a short circuit-specific smoke test only when the goal asks for it or it is needed to prove the workflow starts.

6. Diagnose failure before redesign.
   - Classify failure as code bug, simulator/testbench problem, reward/action issue, memory compatibility issue, insufficient data, or novelty/prior-art uncertainty.
   - Fix code bugs directly when scoped.
   - For design or novelty failures, inspect local papers/materials first, then browse/search if current literature is required.

7. Iterate.
   - Return to mechanism selection with a narrower fix.
   - Stop when the goal's stop condition is satisfied, the budget is reached, or the same blocker repeats three times.

8. Report.
   - Include files changed, commands run, tests passed/failed, commit hash if committed, and remaining risks.
   - State explicitly when full RL/ngspice evaluation was not run.

## Research Lookup Rules

Do not search papers by default. Use paper/material lookup only when:

- the goal explicitly asks for literature;
- an experiment fails for a design reason;
- the novelty boundary is unclear;
- a mechanism resembles known prior art and must be positioned.

Prefer local materials before web search:

- `material/papers_found/paper_index.md`
- `material/papers_found/category_level_llm_td3_idea.md`
- `material/papers_found/cleaned/`
- `docs/paper/`
- user-mentioned papers such as AnalogAgent, AnaFlow, AutoSizer, and OP/DC-to-full optimization papers.

Use the academic-search skill when a coordinated literature search is needed.

## Invariants

- Normal TD3 remains the baseline.
- New LLM/RL behavior must be opt-in through a new workflow path, CLI flag, config, or explicit experimental function.
- Final success must be judged by original strict specs; relaxed targets are allowed only as curriculum or dense reward.
- Do not claim the method is faster until measured against the baseline under comparable budgets.
- Do not transfer topology knowledge blindly inside a category; validate names, dimensions, targets, and compatibility.
- Do not make destructive git changes. Commit only coherent changes and do not push unless asked.
