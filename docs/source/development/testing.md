# Testing

This page documents the repository's automated test suite and the checks used
while developing NLDCSC.

## Contents

- [Install test dependencies](#install-test-dependencies)
- [Run tests](#run-tests)
- [Run focused tests](#run-focused-tests)
- [Coverage and mutation testing](#coverage-and-mutation-testing)
- [Formatting and documentation](#formatting-and-documentation)
- [CI checks](#ci-checks)

## Install test dependencies

Install the package extras and optional test tools from the repository root:

```sh
poetry install --all-extras --with tests
```

The tests use mocks and local fixtures for external services; they should not
require live API, Redis, LDAP, Kafka, or Elasticsearch services.

## Run tests

Run the full suite:

```sh
poetry run pytest
```

Pytest is configured in `pyproject.toml` to run the `tests/` directory and
report line coverage for `nldcsc`. The coverage report is informational; there
is no configured minimum coverage threshold.

## Run focused tests

Run a test file or select tests by name while iterating:

```sh
poetry run pytest tests/test_http_apis.py
poetry run pytest tests/test_data_models.py -k osv
```

The test modules are organized by area:

| Test modules | Coverage area |
|---|---|
| `test_cache_backends.py`, `test_fastapi_cache.py`, `test_redis_cache.py`, `test_cached_api.py` | Cache backends, decorators, and cached API sessions |
| `test_custom_types_and_middleware.py`, `test_datatables.py`, `test_flask_app_manager.py`, `test_flask_components.py`, `test_sso.py` | Flask integrations, middleware, server-side tables, and SSO |
| `test_data_models.py`, `test_doh_geoip.py`, `test_plugins.py`, `test_viper_and_nexpose.py` | Models and service/plugin integrations |
| `test_dcsctransfer.py`, `test_http_api_clients.py`, `test_http_apis.py`, `test_httpx_apis.py` | Synchronous/asynchronous HTTP clients and file transfer |
| `test_ldap_client.py`, `test_logger.py`, `test_generic.py` | Authentication, logging, and shared utilities |
| `test_sql_migrate.py`, `test_sqlalchemy_migrate.py` | SQL migration plugin and Flask migration integration |

`tests/plugins/` contains focused DNS-over-HTTPS and GeoIP tests.
`tests/applications/` contains Flask applications used as fixtures, and
`tests/helpers/` contains shared test helpers.

When checking a single file without the project-wide coverage report, disable
coverage for a shorter output:

```sh
poetry run pytest --no-cov tests/test_data_models.py
```

## Coverage and mutation testing

Coverage is included in the default pytest configuration. To request an
explicit detailed report:

```sh
poetry run pytest --cov=nldcsc --cov-report=term-missing
```

Mutation testing is available through tox:

```sh
tox -e mutmut
```

Mutation scope is intentionally limited by `[tool.mutmut]` in `pyproject.toml`
to covered lines in selected modules. Logger and SQL migration modules are
excluded because their subprocess/import behavior is incompatible with the
current mutation runner setup.

## Formatting and documentation

Format Python files with Black, or check without writing changes:

```sh
poetry run black nldcsc tests
poetry run black --check nldcsc tests
```

Build the Sphinx site:

```sh
poetry run sphinx-build -b html docs/source docs/build/html
```

The repository's contributor instructions also use pre-commit hooks for
formatting and basic file hygiene. Install the hooks with:

```sh
poetry run pre-commit install --hook-type pre-commit --hook-type commit-msg
```

## CI checks

GitHub Actions workflows run the tox test matrix, check Black formatting, build
and publish package artifacts, report coverage, and run mutation testing. See
`.github/workflows/` for the current workflow definitions; `tox.ini` documents
the Python 3.10/3.11 environments and per-module extras.
