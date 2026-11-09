# Usage

This page covers installing NLDCSC and using its reusable modules from an
application. Each module is independent unless its extra explicitly pulls in
another module's dependencies.

## Contents

- [Install the package](#install-the-package)
- [Choose extras](#choose-extras)
- [Use a module](#use-a-module)
- [Available components](#available-components)

## Install the package

Install the base package from PyPI:

```sh
python -m pip install nldcsc
```

The base installation contains the shared package structure but does not
install most integrations. Select one or more extras for the modules used by
your application.

## Choose extras

For example, install the logger and Flask application manager:

```sh
python -m pip install "nldcsc[loggers,flask_managers]"
```

Or install the published `all` extra:

```sh
python -m pip install "nldcsc[all]"
```

See [Configuration](../configuration/index.md#installation-extras) for the
available extra names and their dependency relationships. Prefer a small set
of extras in production so unrelated dependencies are not installed.

## Use a module

Import the component you need from its package path. For example, to use
`AppLogger` as the standard logging class:

```python
import logging

from nldcsc.loggers.app_logger import AppLogger

logging.setLoggerClass(AppLogger)
logger = logging.getLogger(__name__)
logger.info("Application started")
```

Set the logger class before creating named loggers. Logger output destinations
are controlled by environment variables; see
[Runtime settings](../configuration/index.md#runtime-settings).

For a Flask application, create the application in your project and pass it to
the manager:

```python
from flask import Flask

from nldcsc.flask_managers.flask_app_manager import FlaskAppManager

app = Flask(__name__)
manager = FlaskAppManager(version="1.0", app=app)
manager.run()
```

The manager selects the development or production server based on its
configuration. It does not create the Flask application for you.

The SQL migration plugin also provides the `nldcsc db` command group. Install
the `plugin_sql_migrate` extra and inspect its commands with:

```sh
nldcsc db --help
```

## Available components

The [module reference](../reference/index.md) maps all source packages and
submodules. Major areas include:

| Area | Components |
|---|---|
| Application support | Flask app manager, middleware, Flask extensions, SQLAlchemy custom types, and SSO |
| HTTP clients | Shared `requests` and `httpx` clients, cached requests clients, transfer API, and service-specific clients |
| Integrations | LDAP, DNS-over-HTTPS, GeoIP, Hybrid Analysis, WHOIS XML, Nexpose, Viper, and other service clients |
| Data and caching | Redis wrappers and decorators, FastAPI cache coder/backends/decorator, and SQL/Elasticsearch DataTables |
| Logging and utilities | Application/Gunicorn logging, time helpers, generic utilities, and data model types |
| Developer tooling | SQL migration package and CLI |
