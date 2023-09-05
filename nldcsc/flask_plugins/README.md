## Flask plugins

#### expected environment variables and defaults

FlaskEsWrap:
```python
# Account to connect to elasticsearch (only used in Single Elastic connection detail settings)
ELASTIC_USER = os.getenv("ELASTIC_USER", None)
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", None)

# Single Elastic connection details
ELASTIC_SCHEME = os.getenv("ELASTIC_SCHEME", "http")
ELASTIC_HOST = os.getenv("ELASTIC_HOST", "localhost")
ELASTIC_PORT = int(os.getenv("ELASTIC_PORT", 9200))

# Or as a list[str] | list[dict], takes preference over Single elastic connection details settings
# When using this option Authentication should be a part of the connection strings,
# e.g. http://elastic:changeme@localhost:9200/
ELASTIC_CONNECTION_DETAILS = getenv_list("ELASTIC_CONNECTION_DETAILS", None)
ELASTIC_KWARGS = getenv_dict("ELASTIC_KWARGS", None)
```

FlaskKafka
```python
# Url of the kafka server
KAFKA_URL = os.getenv("KAFKA_URL", "localhost:9092")

# Additional kwargs needed for Producer initialization
KAFKA_KWARGS = getenv_dict("KAFKA_KWARGS", None)
```

FlaskRedis
```python
# Url to use when connecting to redis server
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/")

# redis database to use
REDIS_CACHE_DB = int(os.getenv("REDIS_CACHE_DB", 0))

# additional connection parameters
REDIS_KWARGS = getenv_dict("REDIS_KWARGS", None)
```