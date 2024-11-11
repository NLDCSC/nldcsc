from typing import Any, Optional, Union, Dict, TextIO, Sequence

from alembic import util
from alembic.config import Config
from alembic.runtime.environment import (
    EnvironmentContext,
    CompareType,
    CompareServerDefault,
    RenderItemFn,
    ProcessRevisionDirectiveFn,
    IncludeObjectFn,
    IncludeNameFn,
    OnVersionApplyFn,
)
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, URL, MetaData

from ...fractured_alembic.errors.context import ContextNotConfigured
from ...fractured_alembic.runtime.migration import FracturedMigrationContext


class SqlEnvironmentContext(EnvironmentContext):
    def __init__(self, config: Config, script: ScriptDirectory, **kw: Any):
        super().__init__(config, script, **kw)

    def configure(
        self,
        connection: Optional[Connection] = None,
        url: Optional[Union[str, URL]] = None,
        dialect_name: Optional[str] = None,
        dialect_opts: Optional[Dict[str, Any]] = None,
        transactional_ddl: Optional[bool] = None,
        transaction_per_migration: bool = False,
        output_buffer: Optional[TextIO] = None,
        starting_rev: Optional[str] = None,
        tag: Optional[str] = None,
        template_args: Optional[Dict[str, Any]] = None,
        render_as_batch: bool = False,
        target_metadata: Union[MetaData, Sequence[MetaData], None] = None,
        include_name: Optional[IncludeNameFn] = None,
        include_object: Optional[IncludeObjectFn] = None,
        include_schemas: bool = False,
        process_revision_directives: Optional[ProcessRevisionDirectiveFn] = None,
        compare_type: Union[bool, CompareType] = True,
        compare_server_default: Union[bool, CompareServerDefault] = False,
        render_item: Optional[RenderItemFn] = None,
        literal_binds: bool = False,
        upgrade_token: str = "upgrades",
        downgrade_token: str = "downgrades",
        alembic_module_prefix: str = "op.",
        sqlalchemy_module_prefix: str = "sa.",
        user_module_prefix: Optional[str] = None,
        on_version_apply: Optional[OnVersionApplyFn] = None,
        **kw: Any,
    ) -> None:
        opts = self.context_opts
        if transactional_ddl is not None:
            opts["transactional_ddl"] = transactional_ddl
        if output_buffer is not None:
            opts["output_buffer"] = output_buffer
        elif self.config.output_buffer is not None:
            opts["output_buffer"] = self.config.output_buffer
        if starting_rev:
            opts["starting_rev"] = starting_rev
        if tag:
            opts["tag"] = tag
        if template_args and "template_args" in opts:
            opts["template_args"].update(template_args)
        opts["transaction_per_migration"] = transaction_per_migration
        opts["target_metadata"] = target_metadata
        opts["include_name"] = include_name
        opts["include_object"] = include_object
        opts["include_schemas"] = include_schemas
        opts["render_as_batch"] = render_as_batch
        opts["upgrade_token"] = upgrade_token
        opts["downgrade_token"] = downgrade_token
        opts["sqlalchemy_module_prefix"] = sqlalchemy_module_prefix
        opts["alembic_module_prefix"] = alembic_module_prefix
        opts["user_module_prefix"] = user_module_prefix
        opts["literal_binds"] = literal_binds
        opts["process_revision_directives"] = process_revision_directives
        opts["on_version_apply"] = util.to_tuple(on_version_apply, default=())

        if render_item is not None:
            opts["render_item"] = render_item
        opts["compare_type"] = compare_type
        if compare_server_default is not None:
            opts["compare_server_default"] = compare_server_default
        opts["script"] = self.script

        opts.update(kw)

        self._migration_context = FracturedMigrationContext.configure(
            connection=connection,
            url=url,
            dialect_name=dialect_name,
            environment_context=self,
            dialect_opts=dialect_opts,
            opts=opts,
        )

    def get_context(self) -> FracturedMigrationContext:
        if self._migration_context is None:
            raise ContextNotConfigured("No context has been configured yet.")
        return self._migration_context

    def __repr__(self):
        return f"<< {self.__class__.__name__ } >>"
