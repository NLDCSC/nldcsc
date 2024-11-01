from datetime import datetime
import logging
import time
from typing import Any, Tuple, Optional, Dict, Union

from alembic import util
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import (
    MigrationContext,
    HeadMaintainer,
    RevisionStep,
    StampStep,
)
from alembic.util import sqla_compat
from sqlalchemy import (
    Dialect,
    Connection,
    URL,
    Engine,
    literal_column,
)
from sqlalchemy.engine import url as sqla_url
from sqlalchemy.exc import OperationalError

from ...config.constants import schema_migrations_table

log = logging.getLogger(__name__)


class FracturedHeadMaintainer(HeadMaintainer):
    def __init__(self, context: "FracturedMigrationContext", heads: Any) -> None:
        super().__init__(context, heads)

    def update_migration_table(
        self, step: RevisionStep | StampStep, version: int, name: str, duration: int
    ):
        if step.is_upgrade:
            self.insert_migration(version, name, duration)
        else:
            self.remove_migration(version)

    def remove_migration(self, version: int):
        log.debug(f"Remove from migration table {version}")
        self.context.impl._exec(
            self.context._schema_migrations_table.delete().filter(
                self.context._schema_migrations_table.c.version_num == version
            )
        )

    def insert_migration(self, version: int, name: str, duration: int) -> None:
        log.debug(f"Insert into migration table {version}:{name}:{duration}")
        self.context.impl._exec(
            self.context._schema_migrations_table.insert().values(
                version_num=literal_column("'%s'" % version),
                name=literal_column("'%s'" % name),
                duration=literal_column("'%s'" % duration),
                migrated=literal_column("'%s'" % int(time.time())),
            )
        )

    def update_to_step(self, step: RevisionStep | StampStep) -> None:
        if not self.heads:
            self._insert_version(step.revision.revision)
            return

        head, *o = self.heads

        try:
            datetime.strptime(head, "%Y%m%d%H%M%S")
        except ValueError:
            if self.context.is_sync:
                self._update_version(head, step.revision.revision)
                return
            else:
                raise util.CommandError("Invalid revision to update!")

        if step.is_upgrade:
            if step.revision.revision > head:
                log.debug(f"Head update from {head} to {step.revision.revision}")
                self._update_version(head, step.revision.revision)
        else:
            # this function call is a call to the SqlScriptDirectory.get_down_revision.
            down_revision = self.context.script.get_down_revision(
                step.revision.revision
            )

            if down_revision is None:
                log.debug(f"Head update from {head} to None")
                self._delete_version(step.revision.revision)

            elif down_revision < head:
                log.debug(f"Head update from {head} to {down_revision}")
                self._update_version(head, down_revision)

    def __repr__(self):
        return f"<< {self.__class__.__name__ } >>"


class FracturedMigrationContext(MigrationContext):
    """
    This class modifies the MigrationContext so that it can handle scenarios where migrations are fractured.

    A fractured migration context is the cause of working on multiple branches where changes to the db schema can happen simultaneously.
    """

    def __init__(
        self,
        dialect: Dialect,
        connection: Optional[Connection],
        opts: Dict[str, Any],
        environment_context: Optional[EnvironmentContext] = None,
    ):
        self.is_sync = opts.pop("is_sync", False)
        super().__init__(dialect, connection, opts, environment_context)

        self._schema_migrations_table = schema_migrations_table

    def _ensure_schema_migrations_table(self, purge: bool = False):
        with sqla_compat._ensure_scope_for_ddl(self.connection):
            assert self.connection is not None
            self._schema_migrations_table.create(self.connection, checkfirst=True)
            if purge:
                assert self.connection is not None
                self.connection.execute(self._schema_migrations_table.delete())

    def drop_migrations_tables(self):
        with sqla_compat._ensure_scope_for_ddl(self.connection):
            assert self.connection is not None
            try:
                self._version.drop(self.connection)
            except OperationalError:
                pass
            try:
                self._schema_migrations_table.drop(self.connection)
            except OperationalError:
                pass

    def get_full_migrations_table_content(self):
        with sqla_compat._ensure_scope_for_ddl(self.connection):
            assert self.connection is not None
            all_data = self.connection.execute(
                self._schema_migrations_table.select().order_by(
                    self._schema_migrations_table.c["id"]
                )
            ).fetchall()

        return all_data

    @classmethod
    def configure(
        cls,
        connection: Optional[Connection] = None,
        url: Optional[Union[str, URL]] = None,
        dialect_name: Optional[str] = None,
        dialect: Optional[Dialect] = None,
        environment_context: Optional[EnvironmentContext] = None,
        dialect_opts: Optional[Dict[str, str]] = None,
        opts: Optional[Any] = None,
    ) -> MigrationContext:
        if opts is None:
            opts = {}
        if dialect_opts is None:
            dialect_opts = {}

        if connection:
            if isinstance(connection, Engine):
                raise util.CommandError(
                    "'connection' argument to configure() is expected "
                    "to be a sqlalchemy.engine.Connection instance, "
                    "got %r" % connection,
                )

            dialect = connection.dialect
        elif url:
            url_obj = sqla_url.make_url(url)
            dialect = url_obj.get_dialect()(**dialect_opts)
        elif dialect_name:
            url_obj = sqla_url.make_url("%s://" % dialect_name)
            dialect = url_obj.get_dialect()(**dialect_opts)
        elif not dialect:
            raise Exception("Connection, url, or dialect_name is required.")
        assert dialect is not None
        return FracturedMigrationContext(dialect, connection, opts, environment_context)

    def run_migrations(self, **kw: Any) -> None:
        self.impl.start_migrations()

        heads: Tuple[str, ...]
        if self.purge:
            if self.as_sql:
                raise util.CommandError("Can't use --purge with --sql mode")
            self._ensure_version_table(purge=True)
            self._ensure_schema_migrations_table(purge=True)
            heads = ()
        else:
            heads = self.get_current_heads()

            dont_mutate = self.opts.get("dont_mutate", False)

            if not self.as_sql and not heads and not dont_mutate:
                self._ensure_version_table()
                self._ensure_schema_migrations_table()

        head_maintainer = FracturedHeadMaintainer(self, heads)

        assert self._migrations_fn is not None
        for step in self._migrations_fn(heads, self):
            start_time = time.time()
            with self.begin_transaction(_per_migration=True):
                if self.as_sql and not head_maintainer.heads:
                    # for offline mode, include a CREATE TABLE from the base
                    assert self.connection is not None
                    self._version.create(self.connection)
                log.info("Running %s", step)
                if self.as_sql:
                    self.impl.static_output("-- Running %s" % (step.short_log,))
                step.migration_fn(**kw)

                # previously, we wouldn't stamp per migration
                # if we were in a transaction, however given the more
                # complex model that involves any number of inserts
                # and row-targeted updates and deletes, it's simpler for now
                # just to run the operations on every version
                head_maintainer.update_to_step(step)
                for callback in self.on_version_apply_callbacks:
                    callback(
                        ctx=self,
                        step=step.info,
                        heads=set(head_maintainer.heads),
                        run_args=kw,
                    )
                duration = time.time() - start_time

                try:
                    head_maintainer.update_migration_table(
                        step,
                        int(step.insert_version_num),
                        name=step.doc,
                        duration=duration,
                    )
                except ValueError:
                    if self.is_sync:
                        pass
                    else:
                        raise util.CommandError("Invalid revision to update!")

        if self.as_sql and not head_maintainer.heads:
            assert self.connection is not None
            self._version.drop(self.connection)

    # def stamp(self, script_directory: ScriptDirectory, revision: str) -> None: ...

    # NOTE this function should be updated accordingly.

    def __repr__(self):
        return f"<< {self.__class__.__name__ } >>"
