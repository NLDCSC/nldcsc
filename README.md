# NLDCSC package

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