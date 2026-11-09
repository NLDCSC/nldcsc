# Module reference

This reference maps the Python package under `nldcsc/`, including service
clients, integration models, shared infrastructure, and the migration tool.
All non-initializer Python modules are listed below; each package's
`__init__.py` exposes its package-level imports and is represented by that
package's section. The middleware source directory is spelled
`flask_midddleware` in Python imports; its installation extra is
`flask_middleware`.

## Contents

- [Top-level commands and shared utilities](#top-level-commands-and-shared-utilities)
- [Application integration](#application-integration)
- [HTTP APIs](#http-apis)
- [Plugins and data models](#plugins-and-data-models)
- [Caching, tables, and custom types](#caching-tables-and-custom-types)
- [Logging and authentication](#logging-and-authentication)

## Top-level commands and shared utilities

| Source path | Purpose |
|---|---|
| `nldcsc/__main__.py` | Module execution entry point |
| `nldcsc/cli.py` | Click command-line entry point |
| `nldcsc/generic/times.py` | Timestamp and date/time conversion helpers |
| `nldcsc/generic/utils.py` | Environment parsing and reusable utility functions |

## Application integration

| Source path | Purpose |
|---|---|
| `nldcsc/flask_managers/flask_app_manager.py` | Flask app startup and WSGI server management |
| `nldcsc/flask_midddleware/base.py` | Middleware base |
| `nldcsc/flask_midddleware/debug_logging.py` | Request/debug logging middleware |
| `nldcsc/flask_midddleware/middleware_manager.py` | Middleware registration |
| `nldcsc/flask_plugins/flask_eswrap.py` | Flask Elasticsearch/EsWrap integration |
| `nldcsc/flask_plugins/flask_kafka.py` | Flask Kafka producer/consumer integration |
| `nldcsc/flask_plugins/flask_redis.py` | Flask Redis integration |
| `nldcsc/flask_plugins/flask_sql_migrate/__init__.py` | Flask migration extension integration |
| `nldcsc/flask_plugins/flask_sql_migrate/cli.py` | Flask migration commands |
| `nldcsc/flask_plugins/flask_sqlalchemy/__init__.py` | Flask-SQLAlchemy package exports |
| `nldcsc/flask_plugins/flask_sqlalchemy/annotations.py` | SQLAlchemy annotation helpers |
| `nldcsc/flask_plugins/flask_sqlalchemy/custom_types.py` | Flask-SQLAlchemy custom type exports |
| `nldcsc/flask_plugins/flask_sqlalchemy/flask_sqlalchemy.py` | Flask-SQLAlchemy integration |
| `nldcsc/flask_plugins/flask_sqlalchemy/model_base.py` | Flask-SQLAlchemy model base |
| `nldcsc/sql_migrations/flask_sql_migrate.py` | Class-based Flask SQL migration interface |
| `nldcsc/sso/flask_sso/__init__.py` | Flask OpenID Connect SSO integration |
| `nldcsc/sso/flask_sso/sso_views.py` | SSO login, callback, and logout views |
| `nldcsc/sso/monkey_patch/ssl_verification.py` | SSL verification behavior for SSO dependencies |

## HTTP APIs

### Shared clients

| Source path | Purpose |
|---|---|
| `nldcsc/http_apis/base_class/api_base_class.py` | Synchronous `requests` API base |
| `nldcsc/http_apis/base_class/cached_base_class.py` | Cached synchronous API base |
| `nldcsc/httpx_apis/base_class/httpx_base_class.py` | Sync/async `httpx` API base |
| `nldcsc/httpx_apis/dcsctransfer/api.py` | DCSC file-transfer API and upload helpers |

### Service clients and models

| Source path | Purpose |
|---|---|
| `nldcsc/http_apis/confluence/client.py` | Confluence client |
| `nldcsc/http_apis/discord/api.py` | Discord API |
| `nldcsc/http_apis/fbf/client.py` | FBF client |
| `nldcsc/http_apis/fbf/objects.py` | FBF data models |
| `nldcsc/http_apis/mailgun/mail_objects.py` | Mailgun message models |
| `nldcsc/http_apis/mailgun/mailgun_api.py` | Mailgun API |
| `nldcsc/http_apis/nexpose/client.py` | Nexpose API client |
| `nldcsc/http_apis/nexpose/helpers.py` | Nexpose conversion/helpers |
| `nldcsc/http_apis/nexpose/objects.py` | Nexpose response models and enums |
| `nldcsc/http_apis/otrs/otrs_api.py` | OTRS API |
| `nldcsc/http_apis/providentia/providentia_api.py` | Providentia API |
| `nldcsc/http_apis/slack/api.py` | Slack API |
| `nldcsc/http_apis/viper/auth.py` | Viper authentication |
| `nldcsc/http_apis/viper/client.py` | Viper client |
| `nldcsc/http_apis/viper/objects.py` | Viper shared response models |
| `nldcsc/http_apis/viper/collections/bases.py` | Viper collection bases |
| `nldcsc/http_apis/viper/collections/utils.py` | Viper collection utilities |
| `nldcsc/http_apis/viper/collections/admin/__init__.py` | Admin collection |
| `nldcsc/http_apis/viper/collections/admin/objects.py` | Admin collection models |
| `nldcsc/http_apis/viper/collections/async_searches/__init__.py` | Asynchronous search collection |
| `nldcsc/http_apis/viper/collections/auth/__init__.py` | Authentication collection |
| `nldcsc/http_apis/viper/collections/auth/objects.py` | Authentication models |
| `nldcsc/http_apis/viper/collections/general/__init__.py` | General collection |
| `nldcsc/http_apis/viper/collections/general/objects.py` | General collection models |
| `nldcsc/http_apis/viper/collections/kpi/__init__.py` | KPI collection |
| `nldcsc/http_apis/viper/collections/kpi/objects.py` | KPI models |
| `nldcsc/http_apis/viper/collections/nexpose/__init__.py` | Viper Nexpose collection exports |
| `nldcsc/http_apis/viper/collections/nexpose/assets.py` | Nexpose asset collection |
| `nldcsc/http_apis/viper/collections/nexpose/objects.py` | Nexpose collection models |
| `nldcsc/http_apis/viper/collections/nexpose/solutions.py` | Nexpose solution collection |
| `nldcsc/http_apis/viper/collections/nexpose/vulnerabilities.py` | Nexpose vulnerability collection |
| `nldcsc/http_apis/viper/collections/oracledb/__init__.py` | Oracle database collection |
| `nldcsc/http_apis/viper/collections/oracledb/objects.py` | Oracle database models |
| `nldcsc/http_apis/viper/collections/unversioned/__init__.py` | Unversioned Viper collection |
| `nldcsc/http_apis/viper/collections/unversioned/objects.py` | Unversioned response models |
| `nldcsc/http_apis/viper/collections/user/__init__.py` | User collection |
| `nldcsc/http_apis/viper/collections/user/objects.py` | User models |
| `nldcsc/http_apis/viper/collections/v1/__init__.py` | V1 collection |

## Plugins and data models

| Source path | Purpose |
|---|---|
| `nldcsc/plugins/doh/doh_parser.py` | DNS-over-HTTPS request/response parsing |
| `nldcsc/plugins/doh/doh_requester.py` | DNS-over-HTTPS request client |
| `nldcsc/plugins/geoip/api.py` | GeoIP lookup API |
| `nldcsc/plugins/hybrid_analysis/api.py` | Hybrid Analysis API |
| `nldcsc/plugins/hybrid_analysis/objects.py` | Hybrid Analysis data models |
| `nldcsc/plugins/rate_limit/rate_limit.py` | Rate-limiting integration |
| `nldcsc/plugins/redis_client/wrapper.py` | Redis client wrapper |
| `nldcsc/plugins/sql_migrate/__init__.py` | SQL migration engine and public API |
| `nldcsc/plugins/sql_migrate/cli.py` | `nldcsc db` command group |
| `nldcsc/plugins/sql_migrate/config/constants.py` | Migration configuration constants |
| `nldcsc/plugins/sql_migrate/fractured_alembic/errors/context.py` | Migration context errors |
| `nldcsc/plugins/sql_migrate/fractured_alembic/runtime/environment.py` | Custom migration environment |
| `nldcsc/plugins/sql_migrate/fractured_alembic/runtime/migration.py` | Custom migration context |
| `nldcsc/plugins/sql_migrate/fractured_alembic/runtime/op_shell.py` | Migration operation shell |
| `nldcsc/plugins/sql_migrate/fractured_alembic/script/base.py` | Migration script directory and revision handling |
| `nldcsc/plugins/sql_migrate/utils/helpers.py` | Migration helper functions |
| `nldcsc/plugins/vuln_tracker/objects/common.py` | Shared vulnerability data models |
| `nldcsc/plugins/vuln_tracker/objects/csaf.py` | CSAF models |
| `nldcsc/plugins/vuln_tracker/objects/cve_record.py` | CVE Record models |
| `nldcsc/plugins/vuln_tracker/objects/data_class_validations.py` | Data-class validation helpers |
| `nldcsc/plugins/vuln_tracker/objects/nist.py` | NIST NVD models |
| `nldcsc/plugins/vuln_tracker/objects/osv.py` | OSV models |
| `nldcsc/plugins/whoisxml/api.py` | WhoisXML and reverse lookup APIs |
| `nldcsc/plugins/whoisxml/objects/whois.py` | WhoisXML data models |

## Caching, tables, and custom types

| Source path | Purpose |
|---|---|
| `nldcsc/redis_cache/__init__.py` | Redis-backed sync/async caching decorators |
| `nldcsc/fastapi_cache/__init__.py` | FastAPI cache initialization and shared cache operations |
| `nldcsc/fastapi_cache/coder.py` | Cache value encoders/decoders |
| `nldcsc/fastapi_cache/decorator.py` | FastAPI cache decorator |
| `nldcsc/fastapi_cache/backends/base.py` | Cache backend interface |
| `nldcsc/fastapi_cache/backends/redis.py` | Redis cache backend |
| `nldcsc/datatables/server_side_dt.py` | Shared server-side DataTables behavior |
| `nldcsc/datatables/server_side_dt_sql.py` | SQL-backed DataTables |
| `nldcsc/datatables/server_side_dt_es.py` | Elasticsearch-backed DataTables |
| `nldcsc/custom_types/sqlalchemy/annotations.py` | SQLAlchemy annotation types |
| `nldcsc/custom_types/sqlalchemy/custom_types.py` | SQLAlchemy custom column types |
| `nldcsc/custom_types/sqlalchemy/model_base.py` | Shared SQLAlchemy declarative model base |

## Logging and authentication

| Source path | Purpose |
|---|---|
| `nldcsc/loggers/app_logger.py` | Application logger and handlers |
| `nldcsc/loggers/gunicorn_logger.py` | Gunicorn logging integration |
| `nldcsc/loggers/formatters/task_formatter.py` | Task-aware log formatter |
| `nldcsc/loggers/handlers/gelf_handler.py` | GELF UDP handler |
| `nldcsc/loggers/handlers/syslog_handler.py` | Syslog handler |
| `nldcsc/auth/ldap_client.py` | LDAP authentication/client helpers |

For installation dependencies and runtime settings, see
[Configuration](../configuration/index.md). For setup and test commands, see
[Development](../development/index.md) and [Testing](../development/testing.md).
