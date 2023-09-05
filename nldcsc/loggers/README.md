## Loggers

#### expected environment variables and defaults

```python
# If no LOG_FILE_PATH is set, no file logging handler shall be created
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "")

# Log file name
LOG_FILE_NAME = os.getenv("LOG_FILE_NAME", "app.log")

# Set the log level from logging should occur
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Enable syslog
SYSLOG_ENABLE = getenv_bool("SYSLOG_ENABLE", "False")

# If syslog == True; use GELF syslog instead of regular syslog
GELF_SYSLOG = getenv_bool("GELF_SYSLOG", "True")

# GELF format allows for additional fields to be submitted with each log record; Key values of this dict should
# start with underscores; e.g. {"_environment": "SPECIAL"} would append an environment field with the value of
# 'SPECIAL' to each log record.
GELF_SYSLOG_ADDITIONAL_FIELDS = getenv_dict("GELF_SYSLOG_ADDITIONAL_FIELDS", None)

# All syslog communication is, for now, assumed to happen over UDP
# IP address of the syslog server
SYSLOG_SERVER = os.getenv("SYSLOG_SERVER", "127.0.0.1")

# Port of the syslog server
SYSLOG_PORT = int(os.getenv("SYSLOG_PORT", 5140))
```