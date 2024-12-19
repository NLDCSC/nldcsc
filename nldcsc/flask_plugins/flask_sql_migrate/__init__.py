from logging.config import dictConfig

from flask import Flask, current_app
from flask import g
from flask_sqlalchemy import SQLAlchemy

from nldcsc.plugins.sql_migrate.config.constants import LOGGING_CONFIG

from nldcsc.plugins.sql_migrate import Config, SqlMigrate as _SqlMigrate

dictConfig(LOGGING_CONFIG)


class _MigrateConfig(object):
    def __init__(self, migrate: "SqlMigrate", db: SQLAlchemy, **kwargs):
        self.migrate = migrate
        self.db = db
        self.directory = migrate.directory
        self.configure_args = kwargs


class SqlMigrate(_SqlMigrate):
    def __init__(
        self,
        app: Flask = None,
        db: SQLAlchemy = None,
        directory: str = "migrations",
        command: str = "db",
        compare_type: bool = True,
        render_as_batch: bool = True,
        **kwargs,
    ):
        """


        Args:
            app:
            db:
            directory:
            command:
            compare_type:
            render_as_batch:
            **kwargs:
        """

        self.sql_alchemy = db

        super().__init__(
            directory=directory,
            command=command,
            compare_type=compare_type,
            render_as_batch=render_as_batch,
            **kwargs,
        )

        if app is not None and self.sql_alchemy is not None:
            self.init_app(app, self.sql_alchemy, directory)

    def init_app(
        self,
        app: Flask,
        db: SQLAlchemy = None,
        directory: str = None,
        command: str = None,
        compare_type: bool = None,
        render_as_batch: bool = None,
        **kwargs,
    ):
        """


        Args:
            app:
            db:
            directory:
            command:
            compare_type:
            render_as_batch:
            **kwargs:

        Returns:

        """

        self.sql_alchemy = db or self.sql_alchemy
        self.metadata = self.sql_alchemy.metadata

        with app.app_context():
            self.db = self.sql_alchemy.engine

        super().init_app(
            self.db, directory, command, compare_type, render_as_batch, **kwargs
        )

        if not hasattr(app, "extensions"):
            app.extensions = {}

        app.extensions["migrate"] = _MigrateConfig(
            self, self.sql_alchemy, **self.alembic_ctx_kwargs
        )

        from .cli import db as db_cli_group

        app.cli.add_command(db_cli_group, name=self.command)

    def get_config(self, directory=None, x_arg=None, opts=None) -> Config:
        """


        Args:
            directory:
            x_arg:
            opts:

        Returns:

        """

        if x_arg is not None:
            if not isinstance(x_arg, list):
                x_arg = list(x_arg)
            x_arg.extend(getattr(g, "x_arg", []))
        else:
            x_arg = getattr(g, "x_arg", [])

        return super().get_config(directory, x_arg, opts)
