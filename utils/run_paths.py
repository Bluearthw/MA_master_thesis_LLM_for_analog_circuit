from pathlib import Path


def run_artifact_dir(root_dir, circuit_name, run_id):
    """Return the canonical artifact directory for one circuit run."""
    return Path(root_dir) / str(circuit_name) / str(run_id)


def resolve_solution_run_dir(solutions_dir, run_id, circuit_name=None):
    """Find a run in the nested layout, with fallback for legacy flat runs."""
    root = Path(solutions_dir)
    run_name = str(run_id)

    if circuit_name is not None:
        nested = run_artifact_dir(root, circuit_name, run_name)
        if nested.is_dir():
            return nested

    legacy = root / run_name
    if legacy.is_dir():
        return legacy

    matches = []
    if root.is_dir():
        matches = [
            directory / run_name
            for directory in root.iterdir()
            if directory.is_dir() and (directory / run_name).is_dir()
        ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(
            f"Run ID {run_name!r} exists under multiple circuit directories; "
            "specify circuit_name."
        )

    if circuit_name is not None:
        return run_artifact_dir(root, circuit_name, run_name)
    return legacy
