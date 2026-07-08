# TD3 Baseline vs OP/DC-Seeded Sizing Comparison Goal

## Objective

Compare the existing baseline TD3 sizing flow against the new OP/DC+AC-gain seeded TD3 flow on the same circuit set, without changing the sizing implementation during the comparison.

## Methods To Compare

### Baseline TD3

- Uses random full-spec warm-up.
- Uses normal full-reward TD3 training.
- No OP/DC candidate prefiltering.

Suggested preset:

```text
mode = baseline
```

### Proposed TD3

- Runs cheap OP/DC+AC-gain candidate sampling first.
- Ranks candidates using low-fidelity current and DC-gain reward.
- Full-simulates elite candidates.
- Seeds replay with full-reward elite transitions.
- Runs reduced random full-spec warm-up.
- Continues normal full-reward TD3 training.

Suggested preset:

```text
mode = op_seed
```

## Metrics To Record

- Total wall-clock runtime.
- Number of cheap low-fidelity simulations.
- Number of full-spec simulations.
- Best reward reached.
- Step where best reward is first reached.
- Whether all hard constraints are satisfied.
- Final measured specs.
- Best netlist path.
- Warm-start candidate ranking log.
- Seeded full-reward transition log.

## Initial Circuit Set

Start with:

```text
9
```

Then extend to a small same-category amplifier set after the first result is understood.

## Evidence Files

For each run, inspect:

```text
solutions/<run_id>/best_so_far.json
solutions/<run_id>/best_so_far.cir
solutions/<run_id>/pure_RL_best_solution.cir
solutions/<run_id>/warm_start/op_dc_candidates.json
solutions/<run_id>/warm_start/op_dc_seeded_transitions.json
```

For baseline, warm-start files are not expected.

## Comparison Rule

Use the same circuit, random seed, TD3 hyperparameters, target specs, and total training budget unless intentionally running an ablation.

Primary question:

```text
Does OP/DC+AC-gain seeding reach an equal or better best reward with fewer bad early full-spec simulations or lower wall-clock time?
```

Secondary question:

```text
Does the low-fidelity ranking correlate with full-reward quality well enough to justify using it as a warm-start filter?
```

## Stop Condition

The comparison is complete when baseline and proposed runs have been executed on the chosen circuit set, their result files have been summarized in one table, and the result is interpreted as improvement, no improvement, or negative transfer.

## Preliminary Small Comparison

Run date: 2026-07-08

Circuit:

```text
9
```

Commands:

```text
venv\Scripts\python.exe td3_runner.py --circuit_name 9 --run_id compare_small_baseline_9 --seed 123456 --T 30 --w 10 --batch_size 8
venv\Scripts\python.exe td3_runner.py --circuit_name 9 --run_id compare_small_op_seed_9 --seed 123456 --T 30 --w 10 --batch_size 8 --dc_seed_samples 10 --dc_seed_elites 2 --dc_seed_method sobol --full_warmup_steps 10 --warm_start_reduce_random
```

Summary table:

```text
solutions/compare_small_td3_report.md
```

| run_id | runtime_s | full_sims | low_fidelity_sims | cheap_samples | seeded_elites | best_reward | best_step | constraints_met | dc_gain | bandwidth | psrr | input_total_noise | slew_rate | current |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| compare_small_baseline_9 | 7.56269 | 33 | 0 | 0 | 0 | -1.58509 | 28 | False | 10.572 | 1.7595e+07 | 2.05621 | 0.000845638 | 0.00109219 | 0.000396078 |
| compare_small_op_seed_9 | 9.03263 | 35 | 10 | 10 | 2 | -1.63804 | 29 | False | 39.3644 | 3.3986e+06 | 1.65836 | 0.000779671 | 0 | 0.000290754 |

Initial interpretation:

- Baseline achieved slightly better reward in this very small run: -1.58509 vs -1.63804.
- Proposed produced higher DC gain, lower input noise, and lower current, but failed slew rate in the best candidate.
- Neither run satisfied all hard constraints.
- Proposed used 10 cheap OP/DC+AC-gain simulations and 2 more full simulations than baseline in this short setup.
- The two seeded elite candidates showed correct ranking direction in this run: higher low-fidelity reward also had better full reward.

Current conclusion:

```text
Preliminary result is mixed/no improvement at T=30. More seeds or a larger budget are needed before claiming improvement or negative transfer.
```

## Three-Seed Circuit 9 Comparison

Run date: 2026-07-08

Circuit:

```text
9
```

Controlled budget:

```text
T = 100
w = 20
batch_size = 8
seeds = 1, 2, 3
```

Baseline command pattern:

```text
venv\Scripts\python.exe td3_runner.py --circuit_name 9 --run_id compare_s<seed>_baseline_9 --seed <seed> --T 100 --w 20 --batch_size 8
```

Proposed command pattern:

```text
venv\Scripts\python.exe td3_runner.py --circuit_name 9 --run_id compare_s<seed>_op_seed_9 --seed <seed> --T 100 --w 20 --batch_size 8 --dc_seed_samples 16 --dc_seed_elites 4 --dc_seed_method sobol --full_warmup_steps 20 --warm_start_reduce_random
```

Summary table:

```text
solutions/compare_seeded_td3_report.md
```

| run_id | runtime_s | full_sims | low_fidelity_sims | cheap_samples | seeded_elites | best_reward | best_step | constraints_met | dc_gain | bandwidth | psrr | input_total_noise | slew_rate | current |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| compare_s1_baseline_9 | 20.7975 | 110 | 0 | 0 | 0 | -1.5818 | 30 | False | 72.3856 | 1.32897e+06 | 2.01527 | 0.000771467 | 0 | 0.000208393 |
| compare_s1_op_seed_9 | 21.8959 | 114 | 16 | 16 | 4 | -1.54233 | 23 | False | 61.1807 | 3.59668e+06 | 2.38754 | 0.000694124 | 0 | 0.000385111 |
| compare_s2_baseline_9 | 21.6042 | 110 | 0 | 0 | 0 | -2.30386 | 11 | False | 6.76173e-06 | 9.9933e+11 | 4.24645 | 0.136057 | 0 | 8.13073e-10 |
| compare_s2_op_seed_9 | 22.9884 | 114 | 16 | 16 | 4 | -1.41943 | 0 | False | 18.8566 | 1.27913e+07 | 3.27165 | 0.000939494 | 0 | 0.000142267 |
| compare_s3_baseline_9 | 22.3974 | 110 | 0 | 0 | 0 | -1.49254 | 51 | False | 64.8597 | 1.96615e+06 | 2.75877 | 0.000599781 | 0.000575659 | 0.000353904 |
| compare_s3_op_seed_9 | 23.4771 | 114 | 16 | 16 | 4 | -1.49618 | 53 | False | 45.3914 | 4.22618e+06 | 2.8617 | 0.00050056 | 0.00042207 | 0.000724604 |

Aggregate:

| method | mean_runtime_s | mean_full_sims | mean_low_fidelity_sims | mean_best_reward | success_count |
| --- | --- | --- | --- | --- | --- |
| baseline | 21.5997 | 110.0 | 0.0 | -1.79273 | 0/3 |
| op_seed | 22.7872 | 114.0 | 16.0 | -1.48598 | 0/3 |

Reward wins by seed:

| seed | better_method | baseline_best_reward | op_seed_best_reward |
| --- | --- | --- | --- |
| 1 | op_seed | -1.58180 | -1.54233 |
| 2 | op_seed | -2.30386 | -1.41943 |
| 3 | baseline | -1.49254 | -1.49618 |

Interpretation:

- OP/DC+AC-gain seeding improved best reward in 2 of 3 seeds.
- Mean best reward improved from -1.79273 to -1.48598.
- Mean runtime increased from 21.5997 s to 22.7872 s because each proposed run added 16 low-fidelity simulations and 4 full-simulated elite transitions.
- Neither method satisfied all hard constraints within this small T=100 budget.
- The strongest positive signal is seed 2, where baseline selected a nearly off/dead high-bandwidth point while OP/DC+AC-gain seeding found a much more plausible amplifier point.

Current conclusion:

```text
At T=100 on circuit 9, OP/DC+AC-gain seeding improves reward robustness but does not yet reduce wall-clock runtime or achieve full constraint success. The next useful test is either a larger T on circuit 9 or the same 3-seed protocol on another same-category amplifier.
```
