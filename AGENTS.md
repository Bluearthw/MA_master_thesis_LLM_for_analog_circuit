# Repository Agent Instructions

## Working agreement

- Before modifying files, explain the implementation plan in 3-6 concise bullets. Mention the file to be modified.
- Wait for user approval before making major architectural changes.
- Preserve unrelated user changes in the working tree.

## Project conventions

- Run commands from the repository root unless a task requires another directory.
- Use `venv\Scripts\python.exe` for Python checks; the system `python` command may be a Windows Store alias.
- Treat `no_backup/` as temporary runtime storage and `solutions/` as durable output storage.
- Create stable run directories once during environment initialization. Cleanup may remove temporary files, but must not remove output directories or durable best-result files.
- Keep RL observations aligned with the YAML `targets` order and dimension.

## Validation

- After Python edits, run `venv\Scripts\python.exe -m py_compile` on the changed modules.
- Prefer focused tests with reduced or mocked simulation work. Do not start a full RL/ngspice run unless the user requests it.
- Report validation failures and untested behavior explicitly.
