<!--
GENERATED FILE. Do not edit directly.
Edit AGENTS.local.md (repo-specific) or .agent-standards/SHARED.md (shared conventions),
then regenerate with: .agent-standards/build.sh AGENTS.local.md AGENTS.md
-->

# Repository Guide

## Stack And Layout
- Python 3.10/3.11 package managed with Poetry. `setup.py` derives install extras from the `[tool.nldcsc.group.dependencies]` and `[tool.poetry.group.*]` tables in `pyproject.toml` — a new optional module needs both an entry there and a matching Poetry dependency group.
- `nldcsc/` contains the installable modules (e.g. `auth`, `loggers`, `flask_managers`, `flask_plugins`, `http_apis`, `httpx_apis`, `plugins`, `sso`, `sql_migrations`, `redis_cache`, `fastapi_cache`, `custom_types`, `datatables`). Each is installed independently via `pip install nldcsc[<module>]`.
- `tests/` holds one test file per module area (e.g. `test_logger.py`, `test_http_apis.py`, `test_flask_app_manager.py`); there is no `nldcsc/<module>` ↔ `tests/test_<module>.py` naming guarantee, check `tox.ini` for the actual mapping.
- `requirements/default.txt` and `requirements/test.txt` list runtime/test pins used outside Poetry (e.g. by tox); `dev_requirements.txt` is for local dev tooling (currently just `tox`).

## Essential Commands
Run from the repository root:

```bash
poetry install --all-extras
poetry run pytest
poetry run pytest tests/<file>.py::<node-id>
tox                      # full matrix across py310/py311 and per-module extras, see tox.ini
tox -e py311-loggers     # a single tox environment
```

There is no configured linter or formatter (no black/ruff/flake8 config in this repo) — don't assume one.

## Runtime Conventions
- This package has no single entry point; each module under `nldcsc/` is meant to be imported independently by consuming applications. Avoid adding cross-module imports that would force an unrelated extra to be installed.
- Optional dependencies are grouped by Poetry dependency groups and mirrored in `[tool.nldcsc.group.dependencies]` in `pyproject.toml`. When adding a dependency to a module, update both the Poetry group and, if it's a new module, the extras list in `README.md`.
- Version is managed by Poetry (`pyproject.toml` `[tool.poetry].version`); this repo does not auto-derive it from git.

## Module Testing Notes
- `tox.ini` defines per-module test environments (e.g. `-loggers`, `-flask_app`, `-sql_migrate`, `-http_apis`, `-plugins`, `-flask_plugins`) that install only that module's extras before running its test file — prefer the matching tox env when testing a single module in isolation.
- Tests use `mock`/`requests-mock` for external services; there is no live-service test dependency.

## Git Workflow
- Never create commits or push branches/remotes unless explicitly asked. Leave changes in the working tree for the user to review, commit, and push.
- Do not revert or discard unrelated worktree changes.

## Testing Guidelines
- Keep verification proportional to the change. Prefer focused existing tests, syntax checks, or the relevant build/lint command over broad test runs.
- Add tests for meaningful behavior and regressions, not solely to increase coverage or assert boilerplate.

## Documentation Guidelines
- Update relevant user-facing documentation when behavior, configuration, setup, or workflows change.
- Include only information users need, explain it clearly in plain language, and keep it concise and accurate.

## Keeping This File Accurate
- After every implementation, verify that AGENTS.md is still accurate. Update it when project structure or workflows change.
- If AGENTS.md is generated (see the header of this file), edit the source files instead of the generated output.
