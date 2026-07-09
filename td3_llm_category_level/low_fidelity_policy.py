def choose_low_fidelity_policy(transfer_plan):
    """Choose a low-fidelity mode from adapter and memory evidence."""
    if not transfer_plan.get("adapter_valid", False):
        return _policy("skip", "adapter invalid; do not spend OP/DC budget before fallback")

    used = transfer_plan.get("memory_records_used", [])
    rejected = transfer_plan.get("memory_records_rejected", [])

    if not used and not rejected:
        return _policy("pretrain", "no category memory exists; build initial OP/DC evidence")

    if used and not rejected:
        return _policy("probe", "compatible memory exists; use only a small OP/DC check")

    if used and rejected:
        return _policy("probe", "mixed compatible and incompatible memory; probe before trusting transfer")

    if rejected and not used:
        return _policy("probe", "category memory exists but is not directly compatible; probe topology behavior")

    return _policy("pretrain", "default conservative first-run behavior")


def _policy(mode, reason):
    return {
        "mode": mode,
        "reason": reason,
        "implemented_as": _implemented_as(mode),
    }


def _implemented_as(mode):
    if mode == "skip":
        return "disable_low_fidelity_seeding"
    if mode == "probe":
        return "small_op_dc_seed_probe"
    if mode == "gate":
        return "not_yet_supported_by_runner"
    if mode == "pretrain":
        return "larger_op_dc_seed_pretrain"
    return "unknown"


def apply_low_fidelity_policy_to_args(args, policy):
    mode = policy.get("mode", "pretrain")
    if mode == "skip":
        args.dc_seed_samples = 0
        args.dc_seed_elites = 0
        args.full_warmup_steps = 10
        return args

    if mode == "probe":
        args.dc_seed_samples = 8
        args.dc_seed_elites = 2
        args.full_warmup_steps = 8
        return args

    if mode == "gate":
        # True per-candidate gating is a later runner feature. Use probe now.
        args.dc_seed_samples = 8
        args.dc_seed_elites = 2
        args.full_warmup_steps = 8
        return args

    args.dc_seed_samples = 20
    args.dc_seed_elites = 5
    args.full_warmup_steps = 5
    return args
