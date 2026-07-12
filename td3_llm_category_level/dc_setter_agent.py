import json
import math
import re
from pathlib import Path

import numpy as np

from genai_agent.data import response_schema
from td3_llm.warm_start import params_to_action
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


def build_dc_setter_prompt(category, netlist, experience, param_ranges, candidate_count):
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
    }
    return (
        "You are a DC-bias setter for analog circuit sizing. Produce exactly "
        f"{int(candidate_count)} complete parameter candidates. Start from the provided minimum values. "
        "Change bias voltages, bias currents, and multiplicities first. Keep W/L at minimum when bias "
        "controls are sufficient. Change W/L only when heavily required by the topology, for example when "
        "a PMOS normally needs to be wider than a comparable NMOS. Use only provided parameter names and "
        "bounds. Do not include units, rewards, simulated values, or lesson IDs. The increase_dc_gain field "
        "is only your expected direction; low-frequency gain will be measured by AC simulation.\n\n"
        f"INPUT:\n{json.dumps(payload, indent=2)}"
    )


def call_dc_setter_agent(
    category,
    netlist,
    experience,
    param_ranges,
    candidate_count,
    run_id=None,
    circuit_name=None,
    mode="category_llm_rl",
    client=None,
):
    contents = build_dc_setter_prompt(category, netlist, experience, param_ranges, candidate_count)
    if client is None:
        client = agent_utils.get_client()
    return agent_utils.call_agent(
        contents=contents,
        response_schema=response_schema.Struct_dc_setter,
        client=client,
        metrics_run_id=run_id,
        metrics_agent_name="dc_setter",
        metrics_circuit_name=circuit_name,
        metrics_mode=mode,
    )


def prepare_dc_setter_candidates(response, param_ranges, quantize=False):
    raw = _model_to_dict(response)
    raw_candidates = raw.get("candidates", []) if isinstance(raw, dict) else []
    expected_names = list(param_ranges.keys())
    candidates = []
    errors = []
    seen = set()

    minimum_params = {name: float(bounds["min"]) for name, bounds in param_ranges.items()}
    proposed = [
        {"parameters": minimum_params, "increase_dc_gain": False, "source": "minimum_baseline"},
        *raw_candidates,
    ]
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
                "source": candidate.get("source", "llm_dc_setter"),
                "action": params_to_action(validated, param_ranges),
            }
        )
    return candidates, errors


def collect_dc_setter_elites(
    env,
    category,
    candidate_count,
    elite_count,
    strategy="op_ac_domain",
    min_alive_ratio=0.5,
    quantize=False,
    log_path=None,
    client=None,
):
    netlist_path = Path(getattr(env.simulation_engine, "netlist_path", ""))
    if not netlist_path.is_file():
        print(f"[dc_setter] Netlist not found: {netlist_path}")
        return []

    experience, lesson_ids = load_category_experience(category, env.param_ranges.keys())
    try:
        response = call_dc_setter_agent(
            category=resolve_category_name(category),
            netlist=netlist_path.read_text(encoding="utf-8"),
            experience=experience,
            param_ranges=env.param_ranges,
            candidate_count=candidate_count,
            run_id=env.run_id,
            circuit_name=env.circuit_name,
            client=client,
        )
    except Exception as exc:
        print(f"[dc_setter] Agent call failed; using Sobol fallback: {exc}")
        return []

    prepared, errors = prepare_dc_setter_candidates(response, env.param_ranges, quantize=quantize)
    llm_candidate_count = sum(item["source"] == "llm_dc_setter" for item in prepared)
    if llm_candidate_count == 0:
        print("[dc_setter] No valid LLM candidates; using Sobol fallback.")
        return []

    evaluated = []
    rejected = []
    for candidate in prepared:
        action = candidate["action"]
        try:
            op_result = env.evaluate_low_fidelity(action, strategy="op_domain")
            alive_ratio = float(op_result.get("specs", {}).get("op_alive_ratio", 0.0) or 0.0)
            if alive_ratio < float(min_alive_ratio):
                rejected.append({"candidate_id": candidate["candidate_id"], "reason": "op_alive_ratio", "value": alive_ratio})
                continue
            ac_result = env.evaluate_low_fidelity(action, strategy="ac_gain")
            specs = dict(op_result.get("specs", {}))
            specs.update(ac_result.get("specs", {}))
            evaluated.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "action": np.asarray(action, dtype=np.float32),
                    "params": dict(ac_result.get("params", candidate["parameters"])),
                    "specs": specs,
                    "reward": env.dc_feasibility_reward(specs, strategy=strategy),
                    "strategy": strategy,
                    "netlist_path": ac_result.get("netlist_path"),
                    "source": candidate["source"],
                    "increase_dc_gain": candidate["increase_dc_gain"],
                    "lesson_ids": list(lesson_ids),
                }
            )
        except Exception as exc:
            rejected.append({"candidate_id": candidate["candidate_id"], "reason": str(exc)})

    evaluated.sort(key=lambda item: float(item.get("reward", -np.inf)), reverse=True)
    selected = evaluated[: max(0, int(elite_count))]
    _save_log(
        log_path,
        {
            "circuit_name": str(env.circuit_name),
            "run_id": str(env.run_id),
            "category": str(category),
            "lesson_ids": lesson_ids,
            "validation_errors": errors,
            "rejected": rejected,
            "evaluated": [_json_candidate(item) for item in evaluated],
            "selected_elites": [_json_candidate(item) for item in selected],
        },
    )
    print(f"[dc_setter] Selected {len(selected)} elites from {len(evaluated)} OP/AC-feasible candidates.")
    return selected


def _model_to_dict(value):
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return value


def _json_candidate(candidate):
    result = dict(candidate)
    result["action"] = np.asarray(result.get("action", []), dtype=np.float32).tolist()
    return result


def _save_log(path, payload):
    if path is None:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as output_file:
        json.dump(payload, output_file, indent=2, allow_nan=False)
