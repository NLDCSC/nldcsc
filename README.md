# NLDCSC

NLDCSC is a collection of reusable Python components for application
infrastructure, service integrations, and development tooling. Applications
can install the dependencies for only the components they use.

## Contents

- [Functionality](#functionality)
- [Installation and usage](#installation-and-usage)
- [Development](#development)
- [Local documentation](#local-documentation)

## Functionality

- **Application integration:** Flask application management, middleware,
  Elasticsearch, Kafka, Redis and SQLAlchemy extensions, and OpenID Connect SSO.
- **Authentication and logging:** LDAP client, application and Gunicorn logging,
  with optional file, syslog and GELF output.
- **HTTP and integrations:** synchronous and cached `requests` clients,
  synchronous/asynchronous HTTPX clients, DCSC Transfer, DNS-over-HTTPS,
  GeoIP, Hybrid Analysis, WhoisXML, and clients for Confluence, Discord, FBF,
  Mailgun, Nexpose, OTRS, Providentia, Slack and Viper.
- **Data and caching:** Redis and FastAPI caching, server-side DataTables for
  SQL and Elasticsearch, SQLAlchemy custom types, and vulnerability data models
  for CSAF, CVE records, NIST and OSV.
- **Developer tools and utilities:** Flask and Alembic-based SQL migration
  helpers, the `nldcsc db` CLI, rate limiting, and generic date/time and
  environment utilities.

See the [module reference](https://github.com/NLDCSC/nldcsc/blob/master/docs/source/reference/index.md)
for the complete package map.

## Installation and usage

Install the base package and the extras required by your application:

```sh
python -m pip install "nldcsc[loggers,flask_managers]"
```

Alternatively, `python -m pip install "nldcsc[all]"` installs all dependency
groups, including development and documentation tools.

See the [usage guide](https://github.com/NLDCSC/nldcsc/blob/master/docs/source/usage/index.md)
for examples and [configuration](https://github.com/NLDCSC/nldcsc/blob/master/docs/source/configuration/index.md)
for the available extras and runtime settings.

## Development

From the repository root, install the project and contributor dependencies,
then run the tests:

```sh
poetry install --all-extras --with tests,dev,docs
poetry run pytest
```

See the [development guide](https://github.com/NLDCSC/nldcsc/blob/master/docs/source/development/index.md)
and [testing guide](https://github.com/NLDCSC/nldcsc/blob/master/docs/source/development/testing.md)
for repository structure, focused tests and quality checks.

## Local documentation

With the documentation dependency group installed, build the Sphinx site from
the repository root:

```sh
poetry run make -C docs html
```

Open `docs/build/html/index.html` in a browser. The
[documentation source](https://github.com/NLDCSC/nldcsc/blob/master/docs/source/index.md)
links to the full usage, configuration, development, testing and reference guides.
