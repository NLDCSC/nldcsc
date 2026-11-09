# Configuration

NLDCSC is a library rather than an application, so it has no central settings
file or automatic `.env` loader. Configure the individual components through
constructor arguments, Flask application configuration, and the environment
variables listed below. Environment values are read by the component that uses
them; unrelated modules ignore them.

## Contents

- [Installation extras](#installation-extras)
- [Runtime settings](#runtime-settings)
- [Structured environment values](#structured-environment-values)
- [Operational guidance](#operational-guidance)

## Installation extras

`setup.py` builds package extras from the Poetry dependency groups and the
`[tool.nldcsc.group.dependencies]` relationships in `pyproject.toml`.
Underscores in extra names are accepted by pip; the names below match the
project configuration. Each Poetry dependency group is also exposed as an
extra; the aliases in `[tool.nldcsc.group.dependencies]` combine groups.

| Extra | Includes / provides |
|---|---|
| `all` | Every package extra |
| `auth` | LDAP client |
| `cache_fastapi` | FastAPI and Redis dependencies |
| `cache_redis` | Redis cache dependencies |
| `datatables` | Server-side DataTables; includes Flask plugin dependencies |
| `dev` | Local development tools |
| `docs` | Sphinx documentation toolchain |
| `fastapi_cache` | FastAPI cache |
| `flask_managers` | Flask application manager |
| `flask_middleware` | Flask middleware |
| `flask_plugins` | Flask integrations: Elasticsearch, Kafka, Redis, SQLAlchemy, and migration support |
| `http_apis` | Synchronous `requests` API base and clients |
| `http_apis_cached` | Cached synchronous API base |
| `httpx_apis` | Synchronous/asynchronous `httpx` base and transfer API |
| `loggers` | Application and Gunicorn logging |
| `plugin_confluence` | Confluence API client |
| `plugin_doh` | DNS-over-HTTPS parser/requester |
| `plugin_fbf` | FBF API client and models |
| `plugin_geo_ip` | GeoIP API |
| `plugin_limit` | Rate-limit integration dependencies |
| `plugin_mailgun` | Mailgun API and models |
| `plugin_nexpose` | Nexpose client and models |
| `plugin_redis` | Redis client wrapper |
| `plugin_sql_migrate` | SQL migration tooling and `nldcsc` CLI |
| `plugin_viper` | Viper API client and collections |
| `plugin_whoisxml` | WhoisXML API and models |
| `plugins` | Umbrella extra for the plugins listed in `pyproject.toml` |
| `redis_cache` | Redis-backed function cache |
| `sql_migrations` | Flask-SQLAlchemy migration helper |
| `sso` | Flask SSO integration |
| `tests` | Pytest, coverage, mocks, and mutation testing tools |
| `custom_types` | SQLAlchemy custom types and model base |
| `custom_type_sqlalchemy` | SQLAlchemy custom type dependencies |
| `mysql` | MySQL client drivers |

`all` includes every dependency group, including development, documentation,
and test tooling. Prefer the extra matching a module in production rather than
installing `all`. To inspect the exact transitive dependencies, read
`[tool.nldcsc.group.dependencies]` and the matching
`[tool.poetry.group.<name>.dependencies]` in `pyproject.toml`.

## Runtime settings

The following variables are read directly by NLDCSC components. Set values in
the process environment or in the hosting application's configuration system.

| Variable | Component | Default / purpose |
|---|---|---|
| `LOG_LEVEL` | `AppLogger` | `INFO`; logging threshold |
| `LOG_FILE_PATH` | `AppLogger` | Empty; set a directory to enable rotating file output |
| `LOG_FILE_NAME` | `AppLogger` | `app.log` |
| `SYSLOG_ENABLE` | `AppLogger` | `False`; enable syslog output |
| `SYSLOG_SERVER` | `AppLogger` | `127.0.0.1` |
| `SYSLOG_PORT` | `AppLogger` | `5140` |
| `GELF_SYSLOG` | `AppLogger` | `True`; use GELF-formatted syslog when enabled |
| `GELF_SYSLOG_ADDITIONAL_FIELDS` | `AppLogger` | Optional dictionary merged into GELF fields |
| `APP_NAME` | `AppLogger` | `YADA`; syslog/GELF application name |
| `BIND_HOST`, `BIND_PORT` | `FlaskAppManager` | `localhost`, `5050` |
| `DEBUG`, `DEBUG_WITH_SSL` | `FlaskAppManager` | Both `False` |
| `WEB_WORKER_CLASS` | `FlaskAppManager` | `sync` |
| `WEB_MAX_WORKERS` | `FlaskAppManager` | `0` |
| `WEB_WORKER_TIMEOUT` | `FlaskAppManager` | `60` seconds |
| `WEB_TLS_KEY_PATH`, `WEB_TLS_CERT_PATH` | `FlaskAppManager` | `/app/data/certs/key.pem`, `/app/data/certs/cert.pem` |
| `APP_WORKING_DIR` | `FlaskAppManager` | `/app` |
| `LDAP_CACERTFILE` | LDAP client | Optional CA certificate path |
| `SSO_CLIENT_ID`, `SSO_CLIENT_SECRET` | Flask SSO | Client credentials; set secure deployment-specific values |
| `SSO_ISSUER`, `SSO_DISCOVERY_URL` | Flask SSO | Issuer and OpenID discovery URL |
| `SSO_DISCOVERY_KWARGS` | Flask SSO | Optional dictionary passed to discovery |
| `SSO_USERINFO_ENDPOINT`, `SSO_ENDSESSION_ENDPOINT` | Flask SSO | Optional endpoint overrides |
| `SSO_SCOPES` | Flask SSO | `["openid", "profile", "email"]`; must include `openid` |
| `SSO_CODE_CHALLENGE_METHOD` | Flask SSO | `S256` |
| `SSO_OVERWRITE_REDIRECT_URI`, `SSO_CALLBACK_ENDPOINT` | Flask SSO | Optional redirect and callback overrides |
| `SSO_USER_INFO_ENABLED` | Flask SSO | `True` |
| `SSO_TOKEN_ENDPOINT_AUTH_METHOD` | Flask SSO | `client_secret_post` |
| `SSO_TLS_VERIFICATION` | Flask SSO / SSL patch | `True`; keep certificate verification enabled in production |
| `REDIS_SESSION_STORAGE` | Flask SSO | `False`; enable Redis-backed Flask sessions |
| `REDIS_URL`, `REDIS_CACHE_DB`, `REDIS_KWARGS` | Redis wrappers / SSO | Redis connection URL, database index (default `0`), and optional client kwargs |
| `IPGEOLOCATION_ENABLE`, `IPGEOLOCATION_API_KEY` | GeoIP API | Enablement flag and service API key |
| `KAFKA_URL`, `KAFKA_KWARGS` | Flask Kafka extension | `localhost:9092` and optional producer/consumer kwargs |
| `ELASTIC_USER`, `ELASTIC_PASSWORD` | Flask Elasticsearch extension | Optional credentials |
| `ELASTIC_HOST`, `ELASTIC_PORT`, `ELASTIC_SCHEME` | Flask Elasticsearch extension | `localhost`, `9200`, `http` |
| `ELASTIC_COMPAT_VERSION` | Flask Elasticsearch extension | Optional compatibility version |
| `ELASTIC_CONNECTION_DETAILS`, `ELASTIC_KWARGS` | Flask Elasticsearch extension | Optional connection list and client kwargs |

Other settings are supplied as arguments to the relevant constructors or through
the host application's Flask configuration. Consult the corresponding module
in the [module reference](../reference/index.md) for its API.

## Structured environment values

Variables consumed by `getenv_list` or `getenv_dict` use JSON-compatible values.
For example:

```sh
export SSO_SCOPES='["openid", "profile", "email"]'
export REDIS_KWARGS='{"decode_responses": true}'
```

Boolean variables are parsed by `getenv_bool`; use `True` or `False` strings.
Not every component reads every structured setting, and malformed values are
not silently interchangeable with omitted settings.

## Operational guidance

- Never ship the placeholder SSO secret or service credentials in production.
- Keep TLS verification enabled unless a controlled development/test environment
  requires otherwise.
- NLDCSC does not read `.env` files itself. Load environment variables using
  your process manager or application framework.
- See [Usage](../usage/index.md) for installing extras and integrating modules.
