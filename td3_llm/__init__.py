"""Optional TD3 warm-start helpers for category-level sizing experiments."""

from .adapter import (
    build_adapter,
    inspect_adapter,
    load_adapter,
    save_adapter,
    save_validation_result,
    validate_adapter,
)
from .category_memory import save_best_candidate_record
from .low_fidelity_policy import (
    apply_low_fidelity_policy_to_args,
    choose_low_fidelity_policy,
)
from .transfer_plan import (
    build_transfer_plan,
    build_transfer_plan_for_circuit,
    save_transfer_plan,
)
from .warm_start import (
    collect_low_fidelity_elites,
    seed_replay_from_category_memory,
    seed_replay_from_low_fidelity_elites,
)

__all__ = [
    "build_adapter",
    "build_transfer_plan",
    "build_transfer_plan_for_circuit",
    "apply_low_fidelity_policy_to_args",
    "choose_low_fidelity_policy",
    "collect_low_fidelity_elites",
    "inspect_adapter",
    "load_adapter",
    "save_adapter",
    "save_transfer_plan",
    "save_validation_result",
    "save_best_candidate_record",
    "seed_replay_from_category_memory",
    "seed_replay_from_low_fidelity_elites",
    "validate_adapter",
]
