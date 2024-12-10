import argparse
from contextlib import contextmanager
import logging
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from logging.config import dictConfig
from typing import Optional, Dict, List

from alembic import __version__ as __alembic_version__
from alembic import util, migration
from alembic.operations import Operations, BatchOperations
from alembic.migration import RevisionStep
from alembic.autogenerate import RevisionContext
from alembic.config import Config as AlembicConfig
from alembic.runtime.environment import ProcessRevisionDirectiveFn
from alembic.script.revision import _RevIdType
from alembic.util import CommandError
from dataclasses_json import dataclass_json
from dataclasses_json import config as json_config
from sqlalchemy import Engine, MetaData
from sqlalchemy import Row
from sqlalchemy.schema import ColumnCollectionConstraint

from nldcsc.generic.utils import exclude_optional_dict

from .fractured_alembic.runtime.op_shell import (
    create_shell,
)

from .fractured_alembic.runtime.migration import FracturedMigrationContext
from .config.constants import LOGGING_CONFIG, schema_migrations_table
from .fractured_alembic.runtime.environment import SqlEnvironmentContext
from .fractured_alembic.script.base import SqlScriptDirectory, SqlScriptDirectoryContext
from .utils.helpers import timestamp_to_strf_string

dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)

alembic_version = tuple([int(v) for v in __alembic_version__.split(".")[0:3]])

__version__ = "0.1"

_IGNORE_TABLES = ["schema_migrations"]


@dataclass_json
@dataclass
class SchemaMigrationRow:
    id: Optional[int] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    version_num: Optional[int] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    name: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    duration: Optional[float] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    migrated: Optional[int] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def fill_from_row(self, row: Row):
        self.id = row.id
        self.version_num = row.version_num
        self.name = row.name
        self.duration = row.duration
        self.migrated = timestamp_to_strf_string(row.migrated)

    @property
    def get_as_list(self):
        return [self.id, self.version_num, self.name, self.duration, self.migrated]


def catch_errors(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except (CommandError, RuntimeError) as exc:
            logger.error("Error: " + str(exc))
            sys.exit(1)

    return wrapped


class _MigrateConfig(object):
    def __init__(self, migrate: "SqlMigrate", db: Engine, **kwargs):
        self.migrate = migrate
        self.db = db
        self.directory = migrate.directory
        self.configure_args = kwargs


class Config(AlembicConfig):
    def __init__(self, *args, **kwargs):
        self.template_directory = kwargs.pop("template_directory", None)
        super().__init__(*args, **kwargs)

    def get_template_directory(self) -> str:
        """
        Request the path to the template directory.

        Returns:
            Path to the template directory.
        """
        if self.template_directory:
            return self.template_directory
        package_dir = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(package_dir, "templates")

    def __repr__(self):
        return "<< SqlMigrateAlembicConfig >>"


class SqlMigrate(object):
    def __init__(
        self,
        db: Engine = None,
        metadata: MetaData = None,
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
        self.configure_callbacks = []
        self.db = db
        self.command = command
        self.metadata = metadata
        self.directory = str(directory)
        self.alembic_ctx_kwargs = kwargs
        self.alembic_ctx_kwargs["compare_type"] = compare_type
        self.alembic_ctx_kwargs["render_as_batch"] = render_as_batch

        self._dir_path = None
        self._current_config = None

        self._environment_context = None
        self._script_directory = None
        self._script_directory_context = None

        if db is not None:
            self.init_app(db, directory)

    @property
    def environment_context(self) -> SqlEnvironmentContext:
        """
        Get the `SqlEnvironmentContext` for the current app.

        Returns:
            `SqlEnvironmentContext`
        """
        if self._environment_context is None:
            self._environment_context = SqlEnvironmentContext(
                self.current_config, self.script_directory
            )

        return self._environment_context

    @property
    def script_directory(self) -> SqlScriptDirectory:
        """
        Get the `SqlScriptDirectory` for the current app.

        Returns:
            `SqlScriptDirectory`
        """
        if self._script_directory is None:
            self._script_directory = SqlScriptDirectory.from_config(
                self.current_config,
                additional_options={"context": self._script_directory_context},
            )

        return self._script_directory

    @property
    def current_config(self) -> Config:
        """
        Get the `Config` for the current app.

        Returns:
            `Config`
        """
        return self._current_config

    @property
    def migration_context(self) -> FracturedMigrationContext:
        """
        Get the `FracturedMigrationContext` for the current app.

        Returns:
            `FracturedMigrationContext`
        """
        return self.environment_context.get_context()

    @contextmanager
    def _get_env_context(
        self, ctx_opts: dict = None, ensure_migrations_table: bool = False
    ):
        with self.environment_context as env_context:
            connectable = self.db.engine

            if ctx_opts is None:
                ctx_opts = {}

            logger.debug(f"Received context opts {ctx_opts}")

            with connectable.connect() as connection:
                logger.debug(
                    "Configuring migration context from environment context..."
                )
                env_context.configure(
                    connection,
                    self.metadata,
                    **self.alembic_ctx_kwargs,
                    **ctx_opts,
                    include_object=self._include_this_object,
                    process_revision_directives=self._process_revision_directives,
                    target_metadata=self.metadata,
                )

                if ensure_migrations_table:
                    self.migration_context._ensure_schema_migrations_table()

                with env_context.begin_transaction():
                    yield env_context

    @staticmethod
    def generate_rev_id():
        """
        Method to generate a revision id based on the current date and time.

        Returns:
            String with the current revision id.

        Examples:
            20240810131949
        """
        rev_id = datetime.now().strftime("%Y%m%d%H%M%S")
        return rev_id

    def _process_revision_directives(self, context, revision, directives):
        if getattr(self.current_config.cmd_opts, "autogenerate", False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.warning("No changes in schema detected.")

    @staticmethod
    def _include_this_object(object, name, type_, reflected, compare_to) -> bool:
        """
        Method to exclude the custom tables from the migrations / migration scripts

        Args:
            object:
            name: Name of the object to exclude
            type_: Type of the object to exclude
            reflected:
            compare_to:

        Returns:
            True if excluded, False otherwise
        """
        if type_ == "table" and name in _IGNORE_TABLES:
            return False
        return True

    def execute_migration(self, ctx_opts: Optional[dict] = None) -> None:
        """
        Execute migration related actions.

        Args:
            ctx_opts:

        Returns:
            None
        """

        with self._get_env_context(ctx_opts, True) as env_context:
            logger.debug("Running run_migrations in migration context...")
            env_context.run_migrations()

    def init_app(
        self,
        db: Engine = None,
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
        self.db = db or self.db
        self.command = command or self.command
        self.directory = str(directory or self.directory)
        self.alembic_ctx_kwargs.update(kwargs)
        if compare_type is not None:
            self.alembic_ctx_kwargs["compare_type"] = compare_type
        if render_as_batch is not None:
            self.alembic_ctx_kwargs["render_as_batch"] = render_as_batch

        self._script_directory_context = SqlScriptDirectoryContext(
            self.db, schema_migrations_table
        )

        try:
            self.get_config()
        except RuntimeError:
            pass

    def configure(self, f):
        """


        Args:
            f:

        Returns:

        """
        self.configure_callbacks.append(f)
        return f

    def call_configure_callbacks(self, config: Config) -> Config:
        """


        Args:
            config:

        Returns:

        """
        for f in self.configure_callbacks:
            config = f(config)
        return config

    def get_config(self, directory=None, x_arg=None, opts=None) -> Config:
        """


        Args:
            directory:
            x_arg:
            opts:

        Returns:

        """
        if directory is None:
            directory = self.directory
        directory = str(directory)
        config = Config(os.path.join(directory, "alembic.ini"))
        config.set_main_option("script_location", directory)
        if config.cmd_opts is None:
            config.cmd_opts = argparse.Namespace()
        for opt in opts or []:
            setattr(config.cmd_opts, opt, True)
        if not hasattr(config.cmd_opts, "x"):
            setattr(config.cmd_opts, "x", [])
            if x_arg is not None:
                if isinstance(x_arg, list) or isinstance(x_arg, tuple):
                    for x in x_arg:
                        config.cmd_opts.x.append(x)
                else:
                    config.cmd_opts.x.append(x_arg)

        self._current_config = self.call_configure_callbacks(config)

        logger.debug(f"Current config cmd opts: {self.current_config.cmd_opts}")

        return self.current_config

    @catch_errors
    def init(self, directory=None, multidb=False, template=None, package=False):
        """

        Args:
            directory:
            multidb:
            template:
            package:

        Returns:

        """
        logger.debug(f"Received parameters: {locals()}")

        if directory is None:
            directory = self.directory
        template_directory = None
        if template is not None and ("/" in template or "\\" in template):
            template_directory, template = os.path.split(template)
        config = Config(template_directory=template_directory)
        config.set_main_option("script_location", directory)
        config.config_file_name = os.path.join(directory, "alembic.ini")
        config = self._current_config = self.call_configure_callbacks(config)
        if multidb and template is None:
            template = "flask-multidb"
        elif template is None:
            template = "flask"

        if os.access(directory, os.F_OK) and os.listdir(directory):
            raise util.CommandError(
                "Directory %s already exists and is not empty" % directory
            )

        template_dir = os.path.join(config.get_template_directory(), template)
        if not os.access(template_dir, os.F_OK):
            raise util.CommandError("No such template %r" % template)

        if not os.access(directory, os.F_OK):
            logger.info(f"Creating directory {os.path.abspath(directory)!r}")
            os.makedirs(directory)

        versions = os.path.join(directory, "versions")
        logger.info(
            f"Creating directory {os.path.abspath(versions)!r}",
        )
        os.makedirs(versions)

        config_file: str | None = None
        for file_ in os.listdir(template_dir):
            file_path = os.path.join(template_dir, file_)
            if file_ == "alembic.ini.mako":
                assert config.config_file_name is not None
                config_file = os.path.abspath(config.config_file_name)
                if os.access(config_file, os.F_OK):
                    util.msg(
                        f"File {config_file!r} already exists, skipping",
                        **config.messaging_opts,
                    )
                else:
                    self.script_directory._generate_template(
                        file_path, config_file, script_location=directory
                    )
            elif os.path.isfile(file_path):
                output_file = os.path.join(directory, file_)
                self.script_directory._copy_file(file_path, output_file)

        if package:
            for path in [
                os.path.join(os.path.abspath(directory), "__init__.py"),
                os.path.join(os.path.abspath(versions), "__init__.py"),
            ]:
                logger.info(f"Adding {path!r}")
                with open(path, "w"):
                    pass

        assert config_file is not None
        logger.info(
            "Please edit configuration/connection/logging "
            f"settings in {config_file!r} before proceeding.",
        )

    @catch_errors
    def revision(
        self,
        config: Optional[Config] = None,
        message: Optional[str] = None,
        autogenerate: bool = False,
        sql: bool = False,
        head: str = "head",
        splice: bool = False,
        branch_label: Optional[_RevIdType] = None,
        version_path: Optional[str] = None,
        rev_id: Optional[str] = None,
        depends_on: Optional[str] = None,
        process_revision_directives: Optional[ProcessRevisionDirectiveFn] = None,
    ):
        """


        Args:
            config:
            message:
            autogenerate:
            sql:
            head:
            splice:
            branch_label:
            version_path:
            rev_id:
            depends_on:
            process_revision_directives:

        Returns:

        """
        logger.debug(f"Received parameters: {locals()}")

        if rev_id is None:
            rev_id = SqlMigrate.generate_rev_id()

        opts = ["autogenerate"] if autogenerate else None
        config = self.get_config(self.directory, opts=opts)

        command_args = dict(
            message=message,
            autogenerate=autogenerate,
            sql=sql,
            head=head,
            splice=splice,
            branch_label=branch_label,
            version_path=version_path,
            rev_id=rev_id,
            depends_on=depends_on,
        )
        revision_context = RevisionContext(
            config,
            self.script_directory,
            command_args,
            process_revision_directives=process_revision_directives,
        )

        environment = util.asbool(config.get_main_option("revision_environment"))

        if autogenerate:
            environment = True

            if sql:
                raise util.CommandError(
                    "Using --sql with --autogenerate does not make any sense"
                )

            def retrieve_migrations(rev, context):
                revision_context.run_autogenerate(rev, context)
                return []

        elif environment:

            def retrieve_migrations(rev, context):
                revision_context.run_no_autogenerate(rev, context)
                return []

        elif sql:
            raise util.CommandError(
                "Using --sql with the revision command when "
                "revision_environment is not configured does not make any sense"
            )

        if environment:
            self.execute_migration(
                ctx_opts={
                    "fn": retrieve_migrations,
                    "as_sql": sql,
                    "template_args": revision_context.template_args,
                    "revision_context": revision_context,
                }
            )

            # the revision_context now has MigrationScript structure(s) present.
            # these could theoretically be further processed / rewritten *here*,
            # in addition to the hooks present within each run_migrations() call,
            # or at the end of env.py run_migrations_online().

        scripts = [script for script in revision_context.generate_scripts()]

        # set the script_directory back to None -> the property will create a new script_directory when requested.
        self._script_directory = None

        if len(scripts) == 1:
            return scripts[0]
        else:
            return scripts

    @catch_errors
    def migrate(
        self,
        message: Optional[str] = None,
        autogenerate: bool = True,
        sql: bool = False,
        head: str = "head",
        splice: bool = False,
        branch_label: Optional[_RevIdType] = None,
        version_path: Optional[str] = None,
        rev_id: Optional[str] = None,
        depends_on: Optional[str] = None,
        process_revision_directives: Optional[ProcessRevisionDirectiveFn] = None,
        x_arg=None,
    ):
        """
        Alias for 'alembic revision --autogenerate'

        Args:
            message:
            autogenerate:
            sql:
            head:
            splice:
            branch_label:
            version_path:
            rev_id:
            depends_on:
            process_revision_directives:
            x_arg:

        Returns:

        """
        logger.debug(f"Received parameters: {locals()}")

        config = self.get_config(self.directory, opts=["autogenerate"], x_arg=x_arg)

        return self.revision(
            config=config,
            message=message,
            autogenerate=autogenerate,
            sql=sql,
            head=head,
            splice=splice,
            branch_label=branch_label,
            version_path=version_path,
            rev_id=rev_id,
            depends_on=depends_on,
            process_revision_directives=process_revision_directives,
        )

    @catch_errors
    def upgrade(
        self,
        revision: str = "head",
        sql: bool = False,
        tag: Optional[str] = None,
        x_arg=None,
        max_lookback_days: int = 30,
        sync: bool = False,
    ) -> None:
        """


        Args:
            revision:
            sql:
            tag:
            x_arg:
            max_lookback_days

        Returns:

        """
        logger.debug(f"Received parameters: {locals()}")

        self.get_config(
            self.directory, x_arg=x_arg
        )  # This makes sure that self.current_config has the latest values...

        starting_rev = None
        if ":" in revision:
            if not sql:
                raise util.CommandError("Range revision not allowed")
            starting_rev, revision = revision.split(":", 2)

        def upgrade(rev, context):
            revs = []

            if sync:
                revs.extend(self.script_directory._sync_revs(rev))

            new_revs = self.script_directory._upgrade_revs(
                revision, (), max_lookback_days
            )

            revs.extend(new_revs)

            return revs

        self.execute_migration(
            ctx_opts={
                "fn": upgrade,
                "as_sql": sql,
                "is_sync": sync,
                "starting_rev": starting_rev,
                "destination_rev": revision,
                "tag": tag,
            }
        )

    @catch_errors
    def downgrade(
        self,
        revision: str = "-1",
        sql: bool = False,
        tag: Optional[str] = None,
        x_arg=None,
    ) -> None:
        """


        Args:
            revision:
            sql:
            tag:
            x_arg:

        Returns:

        """
        logger.debug(f"Received parameters: {locals()}")

        self.get_config(
            self.directory, x_arg=x_arg
        )  # This makes sure that self.current_config has the latest values...

        starting_rev = None
        if ":" in revision:
            if not sql:
                raise util.CommandError("Range revision not allowed")
            starting_rev, revision = revision.split(":", 2)

        def downgrade(rev, context):
            return self.script_directory._downgrade_revs(revision, rev)

        self.execute_migration(
            ctx_opts={
                "fn": downgrade,
                "as_sql": sql,
                "starting_rev": starting_rev,
                "destination_rev": revision,
                "tag": tag,
            }
        )

    @catch_errors
    def check(
        self, revision: str = None, max_lookback_days: int = 30, sync: bool = False
    ):
        logger.debug(f"Received parameters: {locals()}")

        self.get_config(
            self.directory
        )  # This makes sure that self.current_config has the latest values...

        @dataclass
        class Row:
            rev: RevisionStep

            @property
            def as_list(self):
                revision = self.rev.revision.revision
                name = self.rev.doc

                try:
                    date = datetime.strptime(revision, "%Y%m%d%H%M%S")
                except ValueError:
                    try:
                        date = datetime.strptime(
                            re.search(
                                r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",
                                self.rev.revision.longdoc,
                            ).group(),
                            "%Y-%m-%d %H:%M:%S",
                        )
                    except (AttributeError, ValueError):
                        return [revision, name, None, None]

                age: timedelta = datetime.now() - date
                hours = age.seconds // 3600
                minutes = age.seconds // 60

                if age.days:
                    age = f"{age.days} day{'s' if age.days > 1 else ''}"
                elif hours:
                    age = f"{hours} hour{'s' if hours > 1 else ''}"
                elif minutes:
                    age = f"{minutes} minute{'s' if minutes > 1 else ''}"
                else:
                    age = f"{age.seconds} second{'s' if age.seconds > 1 else ''}"

                return [revision, name, date, age]

        @dataclass
        class IRow:
            instruction: object
            op: object
            args: tuple

            @property
            def as_list(self):
                operation = (
                    self.instruction.__name__.removesuffix("_class")
                    .replace("_", " ")
                    .capitalize()
                )

                first_arg = self.args[0]

                if isinstance(self.op, BatchOperations):
                    first_arg = f"{self.op.impl.table_name}:{first_arg}"

                extra_args = []

                if len(self.args) > 1:
                    for i in range(1, len(self.args)):
                        if isinstance(self.args[i], ColumnCollectionConstraint):
                            try:
                                extra_args.append(
                                    f"{type(self.args[i]).__name__}, {','.join(self.args[i].columns)}"
                                )
                                continue
                            except Exception:
                                pass
                        extra_args.append(str(self.args[i]))

                extra_args = "\n".join(extra_args)

                return [operation, first_arg, extra_args]

        if revision is not None:
            steps = [["Operation", "Argument", "Further arguments"]]

            def cb(cls, operation, *args, **kwargs):
                steps.append(IRow(cls, operation, args).as_list)

            create_shell(None, cb)

            with self._get_env_context() as env_context:
                with Operations.context(env_context._migration_context):
                    step = migration.MigrationStep.upgrade_from_script(
                        self.script_directory.revision_map,
                        self.script_directory.get_revision(str(revision)),
                    )

                    step.migration_fn()

            return steps

        else:
            data = [["rev", "name", "date", "age"]]

            with self._get_env_context() as env_context:
                if sync:
                    revs = self.script_directory._sync_revs(
                        env_context.get_context().get_current_heads()
                    )

                    revs.extend(
                        self.script_directory._upgrade_revs(
                            "head",
                            (),
                            max_lookback_days,
                        )
                    )
                else:
                    revs = self.script_directory._upgrade_revs(
                        "head",
                        env_context.get_context().get_current_heads(),
                        max_lookback_days,
                    )

                for rev in revs:
                    data.append(Row(rev).as_list)

            return data

    def drop(
        self,
    ) -> None:
        """
        Method to drop all tables from the database and remove the migration directory

        Returns:
            None
        """
        logger.debug(f"Received parameters: {locals()}")
        self.get_config(
            self.directory,
        )  # This makes sure that self.current_config has the latest values...

        logger.info("Dropping all tables and migration directory...")

        self.metadata.drop_all(self.db)

        with self._get_env_context() as env_context:
            logger.debug(
                f"Dropping migration tables; context configured: {self.migration_context}"
            )
            self.migration_context.drop_migrations_tables()

        try:
            shutil.rmtree(self.directory, True)
        except Exception:
            logger.error("Failed to drop migration directory.")

        logger.info("Done!!")

    def history(self, include_table_headers: bool = True) -> List[List[str | int]]:
        """
        Method to request the current migration history of the database

        Args:
            include_table_headers: Whether to include the table headers in the output

        Returns:
            List with the migration history of the database
        """
        logger.debug(f"Received parameters: {locals()}")

        self.get_config(
            self.directory,
        )  # This makes sure that self.current_config has the latest values...

        with self._get_env_context() as env_context:
            migration_data = self.migration_context.get_full_migrations_table_content()
            logger.debug(f"Got migration data: {migration_data}")

            if include_table_headers:
                table_data = [
                    [
                        x.name.title()
                        for x in self.migration_context._schema_migrations_table.columns._all_columns
                    ]
                ]
            else:
                table_data = []

            migration_rows = []
            for each in migration_data:
                data = SchemaMigrationRow()
                data.fill_from_row(each)
                migration_rows.append(data.get_as_list)
            table_data.extend(migration_rows)

        return table_data

    @staticmethod
    @catch_errors
    def set_logger_debug_format() -> None:
        """
        Method that sets the logger level to DEBUG and adjusts the log format to include the module names

        Intended to be used primarily from the CLI.

        Returns:
            None
        """
        formatter = logging.Formatter(
            "%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s"
        )
        logger.setLevel(logging.DEBUG)

        logger.handlers[0].setFormatter(formatter)
        logger.handlers[0].setLevel(logging.DEBUG)
        logger.debug("Debug enabled")

    @staticmethod
    @catch_errors
    def get_version(print_stdout: bool = False) -> Dict[str, str]:
        """
        Print the current version of sql_migrate and alembic.

        Args:
            print_stdout: Print to stdout or return object

        Returns:
            Version dictionary containing the current version of sql_migrate and alembic.
        """
        config = Config()
        versions = f"SqlMigrate: {__version__}, Alembic: {__alembic_version__}"
        if print_stdout:
            config.print_stdout(versions)
        else:
            return {"SqlMigrate": __version__, "Alembic": __alembic_version__}

    @staticmethod
    @catch_errors
    def list_templates(print_stdout: bool = False) -> List[str]:
        """
        List available templates.

        Args:
            print_stdout: Print to stdout or return object

        Returns:
            List of available templates strings

        """

        config = Config()
        if print_stdout:
            config.print_stdout("Available templates:\n")
        template_names = []
        for tempname in sorted(os.listdir(config.get_template_directory())):
            template_names.append(tempname)
            with open(
                os.path.join(config.get_template_directory(), tempname, "README")
            ) as readme:
                synopsis = next(readme).strip()
            if print_stdout:
                config.print_stdout("%s - %s", tempname, synopsis)

        return template_names

    def __repr__(self):
        return f"<< {self.__class__.__name__ } >>"
