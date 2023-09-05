## Flask app managers

#### expected environment variables and defaults

```python
# Does the flask app need to run in debug mode
DEBUG = getenv_bool("DEBUG", "False")

# Does the flask app need to run in debug mode with ssl context
DEBUG_WITH_SSL = getenv_bool("DEBUG_WITH_SSL", "False")

# Working directory of the app
APP_WORKING_DIR = os.getenv("APP_WORKING_DIR", "/app")

# Bind app to this IP address
BIND_HOST = os.getenv("BIND_HOST", "localhost")

# Bind app to this port 
BIND_PORT = int(os.getenv("BIND_PORT", 5050))

# Max amount of worker to use for the gunicorn worker; if 0 it defaults to the 
# amount of CPU * 2 + 1
WEB_MAX_WORKERS = int(os.getenv("WEB_MAX_WORKERS", 0))

# Timeout, in seconds, for the gunicorn web workers
WEB_WORKER_TIMEOUT = int(os.getenv("WEB_WORKER_TIMEOUT", 60))

# Path to TLS key path
WEB_TLS_KEY_PATH = os.getenv("WEB_TLS_KEY_PATH", "/app/data/certs/key.pem")

# Path to TLS cert path
WEB_TLS_CERT_PATH = os.getenv("WEB_TLS_CERT_PATH", "/app/data/certs/cert.pem")
```