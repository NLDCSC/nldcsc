from sqlalchemy import BigInteger, Table, MetaData, Column, Integer, String

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "standard": {"format": "%(asctime)s - %(levelname)-8s - %(message)s"},
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",  # Default is stderr
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["default"],
            "level": "WARNING",
            "propagate": False,
        },
        "sqlalchemy.engine": {
            "handlers": ["default"],
            "level": "WARNING",
            "propagate": False,
        },
        "__main__": {  # if __name__ == '__main__'
            "handlers": ["default"],
            "level": "DEBUG",
            "propagate": False,
        },
        "alembic": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "SqlMigrate": {"handlers": ["default"], "level": "INFO", "propagate": False},
    },
}

schema_migrations = "schema_migrations"

schema_migrations_table = Table(
    schema_migrations,
    MetaData(),
    Column("id", Integer, primary_key=True),
    Column("version_num", BigInteger),
    Column("name", String(256)),
    Column("duration", Integer),
    Column("migrated", Integer),
)
