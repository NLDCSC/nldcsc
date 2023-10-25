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
* loggers
* sql_migrations

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
