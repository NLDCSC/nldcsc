# Development

This section describes the NLDCSC library repository, local contributor
workflow, and its test and documentation checks.

## Contents

- [Repository and contribution workflow](#repository-and-contribution-workflow)
- [Local setup](#local-setup)
- [Testing and quality checks](testing.md)

## Repository and contribution workflow

NLDCSC is a Python 3.10/3.11 package managed with Poetry. `nldcsc/` contains
independently installable library modules; `tests/` contains unit tests that
mock external services. Optional dependencies are defined in Poetry groups and
the dependency relationships used to build pip extras are in
`[tool.nldcsc.group.dependencies]` in `pyproject.toml`.

Keep changes focused on the module being changed. Avoid importing an optional
module from an unrelated package area, because consumers install extras
independently. When adding an optional module, update its Poetry dependency
group and extra mapping, relevant tests, and this documentation's
[module reference](../reference/index.md).

Do not commit generated documentation output, credentials, or live-service
fixtures. Preserve unrelated worktree changes. The repository uses
Conventional Commit messages, and commits are not required for local
development.

## Repository layout

| Path | Purpose |
|---|---|
| `nldcsc/` | Installable Python packages; see the complete [module reference](../reference/index.md) |
| `tests/` | Unit tests, test helpers, and local Flask applications |
| `pyproject.toml` | Poetry metadata, dependencies/extras, pytest, and mutation-test configuration |
| `setup.py` | Converts Poetry dependency groups and extra mappings into package metadata |
| `requirements/` | Runtime and test requirement pins used outside Poetry |
| `tox.ini` | Python and per-module test environments |
| `.github/workflows/` | Test, formatting, coverage, mutation, and package-release workflows |
| `docs/` | This Sphinx documentation source and its build entry points |

## Local setup

Install the project, optional integrations, and contributor tools:

```sh
poetry install --all-extras --with tests,dev,docs
```

Run commands from the repository root. See [Testing](testing.md) for focused
test commands, coverage reporting, formatting, and Sphinx builds.

```{toctree}
:hidden:
:maxdepth: 1

testing
```
