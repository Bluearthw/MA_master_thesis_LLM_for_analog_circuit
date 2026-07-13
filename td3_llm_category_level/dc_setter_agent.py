import json
import math
import re
from pathlib import Path

import numpy as np

from genai_agent.data import response_schema
from td3_llm.warm_start import params_to_action, to_jsonable_value
from utils import agent_utils


def load_category_experience(category, param_names, memory_dir=None, max_lessons=8):
    guide_path = Path(
        memory_dir
        or Path("solutions") / "category_memory" / str(category) / "guides" / "category_dc_guide.json"
    )
    if not guide_path.is_file():
        return [], []

    try:
        with open(guide_path, "r", encoding="utf-8") as guide_file:
            lessons = json.load(guide_file).get("lessons", [])
    except (OSError, json.JSONDecodeError, AttributeError):
        return [], []

    names = {str(name).lower() for name in param_names}
    selected = []
    selected_ids = []
    for lesson in lessons:
        if not isinstance(lesson, dict):
            continue
        lesson_text = json.dumps(lesson, sort_keys=True).lower()
        applicable = not names or any(name in lesson_text for name in names)
        applicability = lesson.get("applicability") or {}
        applicable = applicable or bool(applicability.get("category_wide"))
        if not applicable:
            continue
        selected.append(lesson)
        selected_ids.append(str(lesson.get("lesson_id", f"lesson_{len(selected)}")))
        if len(selected) >= max(0, int(max_lessons)):
            break
    return selected, selected_ids


def resolve_category_name(category, categories_dir=None):
    match = re.fullmatch(r"category_?(\d+)", str(category), flags=re.IGNORECASE)
    if not match:
        return str(category)
    category_path = Path(categories_dir or Path("genai_agent") / "data" / "categories" / "jsons")
    category_path = category_path / f"category{match.group(1)}.json"
    try:
        with open(category_path, "r", encoding="utf-8") as category_file:
            return str(json.load(category_file).get("category") or category)
    except (OSError, json.JSONDecodeError, AttributeError):
        return str(category)


def build_dc_setter_prompt(
    category,
    netlist,
    experience,
    param_ranges,
    candidate_count,
    simulation_feedback=None,
    round_index=1,
):
    parameters = {
        name: {
            "minimum": float(bounds["min"]),
            "maximum": float(bounds["max"]),
            "step": float(bounds["step"]),
        }
        for name, bounds in param_ranges.items()
    }
    payload = {
        "category": str(category),
        "netlist": str(netlist),
        "experience": experience,
        "parameters": parameters,
        "simulation_feedback": simulation_feedback or [],
    }
    return (
        "You are an expert in analog circuit sizing acting as a DC-bias setter. "
        f"This is refinement round {int(round_index)}. Produce exactly {int(candidate_count)} complete "
        "parameter candidates that are plausible for the supplied topology. Diagnose the measured OP/AC "
        "feedback before proposing values. Begin from the measured netlist-default candidate or the best "
        "measured candidate, not from every parameter minimum. Jointly choose coupled bias controls to "
        "balance branch currents, preserve saturation, and maintain output headroom. Change bias voltages, "
        "bias currents, and multiplicities first. Keep W/L near the measured reference when bias controls are "
        "sufficient; change W/L only when the topology or measured response justifies it. Do not create a "
        "monotonic sweep. The candidates must represent two distinct, topology-supported hypotheses and "
        "should vary one functional parameter group at a time unless a coupled change is required. Use only "
        "provided parameter names and bounds. Do not include units, invented measurements, rewards, or lesson "
        "IDs. The increase_dc_gain field is only your expected direction; simulation owns the result.\n\n"
        f"INPUT:\n{json.dumps(payload, indent=2)}"
    )


def call_dc_setter_agent(
    category,
    netlist,
    experience,
    param_ranges,
    candidate_count,
    simulation_feedback=None,
    round_index=1,
    run_id=None,
    circuit_name=None,
    mode="category_llm_rl"
):
    contents = build_dc_setter_prompt(
        category,
        netlist,
        experience,
        param_ranges,
        candidate_count,
        simulation_feedback=simulation_feedback,
        round_index=round_index,
    )
    # print("dc_setter agent prompt:\n" + contents)
    return agent_utils.call_agent(
        contents=contents,
        response_schema=response_schema.build_dc_setter_response_schema(param_ranges.keys()),
        metrics_run_id=run_id,
        metrics_agent_name="dc_setter",
        metrics_circuit_name=circuit_name,
        metrics_mode=mode,
    )


def prepare_dc_setter_candidates(
    response,
    param_ranges,
    quantize=False,
    include_minimum_baseline=True,
    source="llm_dc_setter",
):
    raw = _model_to_dict(response)
    raw_candidates = raw.get("candidates", []) if isinstance(raw, dict) else []
    expected_names = list(param_ranges.keys())
    candidates = []
    errors = []
    seen = set()

    minimum_params = {name: float(bounds["min"]) for name, bounds in param_ranges.items()}
    proposed = list(raw_candidates)
    if include_minimum_baseline:
        proposed.insert(
            0,
            {"parameters": minimum_params, "increase_dc_gain": False, "source": "minimum_baseline"},
        )
    for source_index, candidate in enumerate(proposed):
        candidate = _model_to_dict(candidate)
        params = candidate.get("parameters", {}) if isinstance(candidate, dict) else {}
        if set(params) != set(expected_names):
            errors.append(f"candidate[{source_index}] must contain every YAML parameter exactly once")
            continue

        validated = {}
        valid = True
        for name in expected_names:
            try:
                value = float(params[name])
            except (TypeError, ValueError):
                errors.append(f"candidate[{source_index}].{name} is not numeric")
                valid = False
                break
            if not math.isfinite(value):
                errors.append(f"candidate[{source_index}].{name} is not finite")
                valid = False
                break

            bounds = param_ranges[name]
            low = float(bounds["min"])
            high = float(bounds["max"])
            if value < low or value > high:
                errors.append(f"candidate[{source_index}].{name} is outside [{low}, {high}]")
                valid = False
                break
            if quantize:
                step = float(bounds.get("step", 0.0) or 0.0)
                if step > 0.0:
                    value = low + round((value - low) / step) * step
                    value = float(np.clip(value, low, high))
            if "m" in name:
                value = float(int(value))
            validated[name] = value
        if not valid:
            continue

        signature = tuple(validated[name] for name in expected_names)
        if signature in seen:
            continue
        seen.add(signature)
        candidates.append(
            {
                "candidate_id": f"dc_gain_{len(candidates) + 1}",
                "parameters": validated,
                "increase_dc_gain": bool(candidate.get("increase_dc_gain", False)),
                "source": candidate.get("source", source),
                "action": params_to_action(validated, param_ranges),
            }
        )
    return candidates, errors


def collect_dc_setter_elites(
    env,
    category,
    candidate_count,
    elite_count,
    round_count=2,
    strategy="op_ac_domain",
    min_alive_ratio=0.5,
    quantize=False,
    log_path=None
):
    netlist_path = Path(getattr(env.simulation_engine, "netlist_path", ""))
    if not netlist_path.is_file():
        print(f"[dc_setter] Netlist not found: {netlist_path}")
        return []

    experience, lesson_ids = load_category_experience(category, env.param_ranges.keys())
    category_name = resolve_category_name(category)
    netlist_text = netlist_path.read_text(encoding="utf-8")
    evaluated = []
    rejected = []
    validation_errors = []
    round_logs = []
    feedback = []
    seen_signatures = set()
    next_candidate_index = 1
    valid_llm_candidates = 0
    feasible_llm_candidates = 0

    default_params = _netlist_default_params(env)
    default_response = {
        "candidates": [
            {
                "candidate_id": "default",
                "parameters": default_params,
                "increase_dc_gain": False,
            }
        ]
    }
    default_candidates, default_errors = prepare_dc_setter_candidates(
        default_response,
        env.param_ranges,
        quantize=quantize,
        include_minimum_baseline=False,
        source="netlist_default",
    )
    validation_errors.extend(f"default: {error}" for error in default_errors)
    if not default_candidates:
        print("[dc_setter] Netlist defaults are invalid; using Sobol fallback.")
        return []

    default_candidate = default_candidates[0]
    default_candidate["candidate_id"] = "default"
    default_signature = _candidate_signature(default_candidate, env.param_ranges)
    seen_signatures.add(default_signature)
    default_result, default_rejection = _evaluate_dc_candidate(
        env,
        default_candidate,
        strategy,
        min_alive_ratio,
        lesson_ids,
        round_index=0,
    )
    if default_result:
        evaluated.append(default_result)
        feedback.append(_feedback_entry(default_result))
    else:
        rejected.append(default_rejection)
        feedback.append(_feedback_entry(default_rejection))

    for round_index in range(1, max(0, int(round_count)) + 1):
        try:
            response = call_dc_setter_agent(
                category=category_name,
                netlist=netlist_text,
                experience=experience,
                param_ranges=env.param_ranges,
                candidate_count=candidate_count,
                simulation_feedback=list(feedback),
                round_index=round_index,
                run_id=env.run_id,
                circuit_name=env.circuit_name,
            )
            print(response)
        except Exception as exc:
            round_logs.append({"round": round_index, "agent_error": str(exc)})
            print(f"[dc_setter] Round {round_index} agent call failed: {exc}")
            continue

        prepared, errors = prepare_dc_setter_candidates(
            response,
            env.param_ranges,
            quantize=quantize,
            include_minimum_baseline=False,
            source=f"llm_dc_setter_round_{round_index}",
        )
        validation_errors.extend(f"round_{round_index}: {error}" for error in errors)
        accepted_ids = []
        for candidate in prepared:
            signature = _candidate_signature(candidate, env.param_ranges)
            if signature in seen_signatures:
                rejected.append(
                    {
                        "candidate_id": candidate["candidate_id"],
                        "round": round_index,
                        "params": candidate["parameters"],
                        "reason": "duplicate_parameters",
                    }
                )
                continue
            seen_signatures.add(signature)
            candidate["candidate_id"] = f"dc_gain_{next_candidate_index}"
            next_candidate_index += 1
            valid_llm_candidates += 1
            accepted_ids.append(candidate["candidate_id"])
            result, rejection = _evaluate_dc_candidate(
                env,
                candidate,
                strategy,
                min_alive_ratio,
                lesson_ids,
                round_index=round_index,
            )
            if result:
                feasible_llm_candidates += 1
                evaluated.append(result)
                feedback.append(_feedback_entry(result))
            else:
                rejected.append(rejection)
                feedback.append(_feedback_entry(rejection))
        round_logs.append(
            {
                "round": round_index,
                "analysis_summary": str(_model_to_dict(response).get("analysis_summary", "")),
                "accepted_candidate_ids": accepted_ids,
                "feedback_after_round": list(feedback),
            }
        )

    if valid_llm_candidates == 0 or feasible_llm_candidates == 0:
        print("[dc_setter] No OP/AC-feasible LLM candidates across refinement rounds; using Sobol fallback.")
        return []

    evaluated.sort(key=lambda item: float(item.get("reward", -np.inf)), reverse=True)
    selected = evaluated[: max(0, int(elite_count))]
    _save_log(
        log_path,
        {
            "circuit_name": str(env.circuit_name),
            "run_id": str(env.run_id),
            "category": str(category),
            "lesson_ids": lesson_ids,
            "round_count": int(round_count),
            "candidates_per_round": int(candidate_count),
            "validation_errors": validation_errors,
            "rounds": round_logs,
            "rejected": rejected,
            "evaluated": [_json_candidate(item) for item in evaluated],
            "selected_elites": [_json_candidate(item) for item in selected],
        },
    )
    print(f"[dc_setter] Selected {len(selected)} elites from {len(evaluated)} OP/AC-feasible candidates.")
    return selected


def _netlist_default_params(env):
    defaults = getattr(env.simulation_engine, "parameters", {}) or {}
    return {
        name: float(defaults.get(name, bounds["min"]))
        for name, bounds in env.param_ranges.items()
    }


def _candidate_signature(candidate, param_ranges):
    return tuple(float(candidate["parameters"][name]) for name in param_ranges)


def _evaluate_dc_candidate(env, candidate, strategy, min_alive_ratio, lesson_ids, round_index):
    action = candidate["action"]
    try:
        op_result = env.evaluate_low_fidelity(action, strategy="op_domain")
        op_specs = dict(op_result.get("specs", {}))
        alive_ratio = float(op_specs.get("op_alive_ratio", 0.0) or 0.0)
        if alive_ratio < float(min_alive_ratio):
            return None, {
                "candidate_id": candidate["candidate_id"],
                "round": int(round_index),
                "params": dict(op_result.get("params", candidate["parameters"])),
                "specs": op_specs,
                "reason": "op_alive_ratio",
                "value": alive_ratio,
                "source": candidate["source"],
            }
        ac_result = env.evaluate_low_fidelity(action, strategy="ac_gain")
        specs = dict(op_specs)
        specs.update(ac_result.get("specs", {}))
        return {
            "candidate_id": candidate["candidate_id"],
            "round": int(round_index),
            "action": np.asarray(action, dtype=np.float32),
            "params": dict(ac_result.get("params", candidate["parameters"])),
            "specs": specs,
            "reward": env.dc_feasibility_reward(specs, strategy=strategy),
            "strategy": strategy,
            "netlist_path": ac_result.get("netlist_path"),
            "source": candidate["source"],
            "increase_dc_gain": candidate["increase_dc_gain"],
            "lesson_ids": list(lesson_ids),
        }, None
    except Exception as exc:
        return None, {
            "candidate_id": candidate["candidate_id"],
            "round": int(round_index),
            "params": dict(candidate["parameters"]),
            "specs": {},
            "reason": str(exc),
            "source": candidate["source"],
        }


def _feedback_entry(result):
    return {
        "candidate_id": str(result.get("candidate_id")),
        "round": int(result.get("round", 0)),
        "status": "evaluated" if "reward" in result else "rejected",
        "parameters": to_jsonable_value(result.get("params", {})),
        "measured": to_jsonable_value(result.get("specs", {})),
        "reward": float(result["reward"]) if "reward" in result else None,
        "rejection_reason": result.get("reason"),
    }


def _model_to_dict(value):
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return value


def _json_candidate(candidate):
    return to_jsonable_value(candidate)


def _save_log(path, payload):
    if path is None:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as output_file:
        json.dump(payload, output_file, indent=2, allow_nan=False)
