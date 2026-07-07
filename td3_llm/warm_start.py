import numpy as np

from .category_memory import is_compatible, iter_records


def params_to_action(params, param_ranges):
    action = []
    for name, bounds in param_ranges.items():
        if name not in params:
            raise KeyError(f"Missing saved parameter '{name}'")

        min_val = float(bounds["min"])
        max_val = float(bounds["max"])
        if max_val == min_val:
            action.append(0.0)
            continue

        value = float(params[name])
        normalized = 2.0 * (value - min_val) / (max_val - min_val) - 1.0
        action.append(float(np.clip(normalized, -1.0, 1.0)))

    return np.asarray(action, dtype=np.float32)


def _evaluate_seed_action(env, action):
    env.evaluate(action)
    reward, hard_satisfied = env.reward_computation(env.cur_norm_specs)
    env._save_best_candidate(reward, hard_satisfied)
    observation = env._build_observation(env.cur_norm_specs)
    return observation, reward


def seed_replay_from_category_memory(env, replay_buffer, category, max_records=20, memory_dir=None):
    compatible = []
    for record in iter_records(category, memory_dir):
        if is_compatible(record, env):
            compatible.append(record)

    compatible.sort(key=lambda item: float(item.get("reward", -np.inf)), reverse=True)
    selected = compatible[: max(0, int(max_records))]

    seeded = 0
    for record in selected:
        try:
            action = params_to_action(record.get("params", {}), env.param_ranges)
            next_observation, reward = _evaluate_seed_action(env, action)
        except Exception as exc:
            print(f"[td3_llm] Failed to seed memory record: {exc}")
            continue

        state = np.zeros(env.observation_space.shape[0], dtype=np.float32)
        done = True
        replay_buffer.push(state, action, reward, next_observation, done)
        seeded += 1

    if category:
        print(
            f"[td3_llm] Seeded {seeded} replay transitions from "
            f"{len(compatible)} compatible '{category}' memory records."
        )
    return seeded
