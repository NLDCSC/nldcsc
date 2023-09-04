## Loggers

#### expected environment variables and defaults

```
# If no LOG_FILE_PATH is set, no file logging handler shall be created
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "")

LOG_FILE_NAME = os.getenv("LOG_FILE_NAME", "app.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

SYSLOG_ENABLE = getenv_bool("SYSLOG_ENABLE", "False")
GELF_SYSLOG = getenv_bool("GELF_SYSLOG", "True")

# GELF format allows for additional fields to be submitted with each log record; Key values of this dict should
# start with underscores; e.g. {"_environment": "SPECIAL"} would append an environment field with the value of
# 'SPECIAL' to each log record.
GELF_SYSLOG_ADDITIONAL_FIELDS = getenv_dict("GELF_SYSLOG_ADDITIONAL_FIELDS", None)

SYSLOG_SERVER = os.getenv("SYSLOG_SERVER", "127.0.0.1")
SYSLOG_PORT = int(os.getenv("SYSLOG_PORT", 5140))
```