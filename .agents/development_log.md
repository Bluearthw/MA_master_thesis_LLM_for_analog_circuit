# Development Log

## 2026-07-12

- Added the minimal category-level LLM DC Setter candidate source.
- Kept baseline TD3 unchanged; `category_llm_rl` always attempts the Setter.
- Added deterministic validation, minimum-value baseline, OP gating, AC-gain evaluation, and Sobol fallback.
- Added focused mocked tests; no real LLM, ngspice, or full RL run was started.
- Unified policy and seed full-candidate recording and added simulation, solution-time, LLM-time, and wall-time metrics.
- Replaced the DC Setter's open parameter dictionary at call time with a circuit-specific closed response schema.
- Reused recursive NumPy conversion for JSON-safe DC Setter candidate logs.
- Added two-round DC Setter refinement: simulate defaults, propose two candidates, feed results back, and propose two refinements.
