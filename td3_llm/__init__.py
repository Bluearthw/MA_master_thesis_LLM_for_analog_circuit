"""Optional TD3 warm-start helpers for category-level sizing experiments."""

from .adapter import (
    build_adapter,
    inspect_adapter,
    load_adapter,
    save_adapter,
)
from .category_memory import save_best_candidate_record
from .warm_start import (
    collect_low_fidelity_elites,
    seed_replay_from_category_memory,
    seed_replay_from_low_fidelity_elites,
)

__all__ = [
    "build_adapter",
    "collect_low_fidelity_elites",
    "inspect_adapter",
    "load_adapter",
    "save_adapter",
    "save_best_candidate_record",
    "seed_replay_from_category_memory",
    "seed_replay_from_low_fidelity_elites",
]
