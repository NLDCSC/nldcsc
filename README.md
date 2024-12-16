# NLDCSC package

[![GitHub Release](https://img.shields.io/github/release/NLDCSC/nldcsc.svg?style=flat)]()
[![GPLv3 License](https://img.shields.io/badge/License-GPL%20v3-yellow.svg)](https://opensource.org/licenses/)

[![codecov](https://codecov.io/gh/NLDCSC/nldcsc/graph/badge.svg?token=QSHW4B6ADR)](https://codecov.io/gh/NLDCSC/nldcsc)
![pypi](https://github.com/NLDCSC/nldcsc/actions/workflows/package_to_pypi.yaml/badge.svg)
![pytest](https://github.com/NLDCSC/nldcsc/actions/workflows/tox_tests.yaml/badge.svg)

This package contains generic re-usable code.

Install the full package:

```
pip install nldcsc[all]
```

Package has several modules which can be installed separately by specifying them 
as an extra requirement. To install the loggers module only, specify:

```
pip install nldcsc[loggers]
```
Or for multiple modules:
```
pip install nldcsc[loggers, flask_managers]
```

## Modules

The following modules are available in the nldcsc package:

* auth
* datatables
* flask_managers
* flask_middleware
* flask_plugins
* http_apis
* httpx_apis
* loggers
* sql_migrations
* sso
* plugins
    - plugin_doh
    - plugin_geo_ip
    - plugin_sql_migrate
    - plugin_redis
* custom_types
    - custom_type_sqlalchemy

### Loggers

There are two loggers provided:
* AppLogger (nldcsc.loggers.app_logger.AppLogger)
* GunicornLogger (nldcsc.loggers.app_logger.GunicornLogger)

The AppLogger is intended to be used as a loggerClass to be used for the 
standard python logging module.

```python
import logging
from nldcsc.loggers.app_logger import AppLogger

logging.setLoggerClass(AppLogger)

mylogger = logging.getLogger(__name__)
```
The 'mylogger' instance has all the proper formatting and handlers 
(according to the desired config) to log messages.

The Gunicorn logger is intended to be used for as a loggerClass for the 
gunicorn webserver; it enables the FlaskAppManager to set the necessary 
formatting and handles according to the AppLogger specs and a custom format
for the gunicorn access logging.

### Flask app manager

The FlaskAppManager is intended to be used to 'run' flask applications in 
both test, development as in production environments. 

```python
from YADA import app
from nldcsc.flask_managers.flask_app_manager import FlaskAppManager

fam = FlaskAppManager(version="1.0", app=app)
fam.run()
```
Depending on the configuration the FlaskAppManager uses a werkzeug (DEBUG == True)
or a gunicorn webserver. TLS could be set for both webservers iaw the module specific
README.md.

### HTTP apis

Baseclass for http api communication is present under 
nldcsc.http_apis.base_class.api_base_class.ApiBaseClass

### HTTPX apis

Baseclass for httpx api communication is present under 
nldcsc.httpx_apis.base_class.httpx_base_class.HTTPXBaseClass

### SQL Migrations

The sql migrations can be used to facilitate migration between different
versions of sql models / versions. It relies on flask migrate to perform
the different migrations. It has a CLI as well as an python class based API.

Check the command line help
```
python3 -m nldcsc.sql_migrations.flask_sql_migrate -a /path/to/script_with_flask_app.py -i
python3 -m nldcsc.sql_migrations.flask_sql_migrate -a /path/to/script_with_flask_app.py -m
python3 -m nldcsc.sql_migrations.flask_sql_migrate -a /path/to/script_with_flask_app.py -u
```

Or initiate the FlaskSqlMigrate as a class and initiate the migration 
process from there: 
```python
from nldcsc.sql_migrations.flask_sql_migrate import FlaskSqlMigrate
fsm = FlaskSqlMigrate(app_ref="/path/to/script_with_flask_app.py")

fsm.db_init()
fsm.db_migrate()
fsm.db_update()
```

### Plugins

There are several off the shelf plugins that can be used in other projects. Every plugin can be installed with:
```
pip install nldcsc[plugin-<plugin-name>]
```
or if you rather install all the plugins:
```
pip install nldcsc[plugins]
```

#### plugin-sql-migrate

The sql_migrate plugin serves as a wrapper around alembic but replaces the naming convention of migration files to support multiple branches of development. To make use of this plugin the CLI can be used.

Check the command line help
```
python3 -m nldcsc db --help
```
OR
```
nldcsc db --help
```

The plugin expects to be pointed towards a python configuration file that looks something like this:
```python
from my_awesome_project.db import get_engine
from my_awesome_project.models.base import ModelBase

#This should be a SQLAlchemy engine object.
db = get_engine()

#This should be the modelbase class metadata
metadata = ModelBase.metadata
```

### Custom types

Custom types is a collection of custom types or objects that can be used with other libraries

#### custom_type_sqlalchemy

This is a collection of types to be used together with sqlalchemy. If these types are to be used make sure to inherit from the ModelBase within the NLDCSC package. As the types get mapped to their SQL equivalents there.

## Adding modules and/or groups

Everything for this package is defined in the pyproject.toml file. Dependencies are managed by poetry and grouped in, you guessed it, groups. Every poetry group can be installed as an extra using pip. 

Extra extras or group on group/extra dependencies can also be defined in the [tool.nldcsc.group.dependencies] section. Everything defined here will also become an extra if no group already exists. You can use everything defined here as dependency for another group, order does **not** matter.

example:
```toml
[tool.nldcsc.group.dependencies]
my_awesome_extra = ["my_awesome_group", "my_other_group"]
my_awesome_group = ["my_logging_group"]

[tool.poetry.group.my_awesome_group.dependencies]
<dependency here>

[tool.poetry.group.my_other_group.dependencies]
<dependency here>

[tool.poetry.group.my_logging_group.dependencies]
<dependency here>
```

Using this example the following extras exist with the correct dependencies:
```
pip install nldcsc[all]
pip install nldcsc[my-awesome-extra]
pip install nldcsc[my-awesome-group]
pip install nldcsc[my-other-group]
pip install nldcsc[my-logging-group]
```
