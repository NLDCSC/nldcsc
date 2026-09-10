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
tox -e mutmut            # mutation testing, see Module Testing Notes below
```

There is no configured linter or formatter (no black/ruff/flake8 config in this repo) — don't assume one.

## Runtime Conventions
- This package has no single entry point; each module under `nldcsc/` is meant to be imported independently by consuming applications. Avoid adding cross-module imports that would force an unrelated extra to be installed.
- Optional dependencies are grouped by Poetry dependency groups and mirrored in `[tool.nldcsc.group.dependencies]` in `pyproject.toml`. When adding a dependency to a module, update both the Poetry group and, if it's a new module, the extras list in `README.md`.
- Version is managed by Poetry (`pyproject.toml` `[tool.poetry].version`); this repo does not auto-derive it from git.

## Module Testing Notes
- `tox.ini` defines per-module test environments (e.g. `-loggers`, `-flask_app`, `-sql_migrate`, `-http_apis`, `-plugins`, `-flask_plugins`) that install only that module's extras before running its test file — prefer the matching tox env when testing a single module in isolation.
- Tests use `mock`/`requests-mock` for external services; there is no live-service test dependency.
- Mutation testing runs via `mutmut` (config in `pyproject.toml` `[tool.mutmut]`, `tox -e mutmut`, `.github/workflows/mutation_testing.yaml` on PRs — report-only, does not block merges). Scope is intentionally limited to modules with meaningful existing coverage (`generic`, `http_apis/base_class`, `flask_plugins/flask_sql_migrate`, `plugins/sql_migrate`) plus `mutate_only_covered_lines = true`. `nldcsc/loggers` and `nldcsc/sql_migrations` are excluded — their tests reimport nldcsc modules via a fresh `flask` CLI subprocess or mutate global logging state, which breaks under mutmut's import-shadowed `mutants/` tree. When expanding scope to a new module, verify its tests still pass under `tox -e mutmut` before adding it to `only_mutate`.
