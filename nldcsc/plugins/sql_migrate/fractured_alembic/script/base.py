from datetime import datetime, timedelta
import logging
import os
import shutil
from collections import deque
from dataclasses import dataclass
from typing import Generator, List, Mapping, Optional, Any

from alembic import migration, util
from alembic.config import MessagingOptions
from alembic.migration import RevisionStep
from alembic.script import ScriptDirectory
from alembic.util import sqla_compat
from sqlalchemy import Table
from sqlalchemy.orm import Session
from sqlalchemy.exc import DatabaseError

logger = logging.getLogger(__name__)


@dataclass
class SqlScriptDirectoryContext:
    db: Session
    table: Table
    revision_column: Optional[str] = "version_num"


class SqlScriptDirectory(ScriptDirectory):
    def __init__(
        self,
        dir: str,
        file_template: str = ...,
        truncate_slug_length: int | None = 40,
        version_locations: List[str] | None = None,
        sourceless: bool = False,
        output_encoding: str = "utf-8",
        timezone: str | None = None,
        hook_config: Mapping[str, str] | None = None,
        recursive_version_locations: bool = False,
        messaging_opts: MessagingOptions = ...,
        context: SqlScriptDirectoryContext | None = None,
        **kwargs,
    ) -> None:
        """
        This inits the SqlScriptDirectory

        Any leftover **kwargs get lost and is only present for compatibility reasons.
        """
        super().__init__(
            dir,
            file_template,
            truncate_slug_length,
            version_locations,
            sourceless,
            output_encoding,
            timezone,
            hook_config,
            recursive_version_locations,
            messaging_opts,
        )
        self.context = context

        assert self.context is not None
        self.create_diff_queue()

    def get_down_revisions(self, revision: str) -> List[int]:
        connectable = self.context.db.engine

        with connectable.connect() as connection:
            with sqla_compat._ensure_scope_for_ddl(connection):
                assert connection is not None

                down_revs = connection.execute(
                    self.context.table.select()
                    .order_by(self.context.table.c[self.context.revision_column].desc())
                    .filter(
                        self.context.table.c[self.context.revision_column] > revision
                    )
                ).fetchall()

                logger.debug(f"Got {len(down_revs)} revs to downgrade to {revision}")

                return [
                    getattr(down_rev, self.context.revision_column)
                    for down_rev in down_revs
                ]

    def get_down_revisions_steps(self, steps: int) -> List[int]:
        connectable = self.context.db.engine

        with connectable.connect() as connection:
            with sqla_compat._ensure_scope_for_ddl(connection):
                assert connection is not None

                down_revs = connection.execute(
                    self.context.table.select()
                    .order_by(self.context.table.c[self.context.revision_column].desc())
                    .limit(steps)
                ).fetchall()

                logger.debug(
                    f"Got {len(down_revs)} revs to downgrade; requested {steps}"
                )

                return [
                    getattr(down_rev, self.context.revision_column)
                    for down_rev in down_revs
                ]

    def get_down_revision(self, revision: str) -> str | None:
        connectable = self.context.db.engine

        with connectable.connect() as connection:
            with sqla_compat._ensure_scope_for_ddl(connection):
                assert connection is not None

                down_rev = connection.execute(
                    self.context.table.select()
                    .filter(
                        self.context.table.c[self.context.revision_column] < revision
                    )
                    .order_by(self.context.table.c[self.context.revision_column].desc())
                ).fetchone()

                logger.debug(f"Down revision of {revision} is {down_rev}")

                if not down_rev:
                    return None

                return str(getattr(down_rev, self.context.revision_column))

    def create_diff_queue(self) -> None:
        self.missing_migrations = deque()

        connectable = self.context.db.engine

        with connectable.connect() as connection:
            with sqla_compat._ensure_scope_for_ddl(connection):
                assert connection is not None

                for revision in self._load_revisions():
                    try:
                        datetime.strptime(revision.revision, "%Y%m%d%H%M%S")
                    except ValueError:
                        logger.debug(f"The revision {revision.revision} is unsupported")
                        continue

                    try:
                        entry = connection.execute(
                            self.context.table.select().filter(
                                self.context.table.c[self.context.revision_column]
                                == revision.revision
                            )
                        ).fetchone()
                    except DatabaseError:
                        # no table exists yet
                        entry = None

                    # the revision should depend on nothing
                    revision._normalized_resolved_dependencies = ()

                    if not entry or not entry.migrated:
                        self.missing_migrations.append(revision)
                        logger.debug(
                            f"Found revision {revision.revision} not present in db!"
                        )

                self.missing_migrations = sorted(
                    self.missing_migrations, key=lambda r: int(r.revision)
                )

    def consume_missing_queue(self) -> Generator[str, None, None]:
        try:
            yield self.missing_migrations.popleft()
        except IndexError:
            raise StopIteration

    def _sync_revs(self, current_rev):
        def can_sync(rev):
            try:
                datetime.strptime(rev, "%Y%m%d%H%M%S")
            except ValueError:
                return True
            return False

        if isinstance(current_rev, tuple) and current_rev:
            current_rev, *o = current_rev

        if current_rev:
            if not can_sync(current_rev):
                raise util.CommandError("Can't sync with new migrations applied!")

        migrations = []

        for rev in super()._upgrade_revs("head", (current_rev,)):
            if can_sync(rev.revision.revision):
                migrations.append(rev)

        return migrations

    def _upgrade_revs(
        self,
        destination: str,
        current_rev: str | tuple[str],
        max_lookback_days: int,
    ) -> List[RevisionStep]:
        if isinstance(current_rev, tuple) and current_rev:
            current_rev, *o = current_rev

        if max_lookback_days != -1 and current_rev:
            current = datetime.strptime(current_rev, "%Y%m%d%H%M%S")

            oldest_allowed_revision = (
                current - timedelta(days=max_lookback_days)
            ).strftime("%Y%m%d%H%M%S")

        revisions = []

        for script in self.missing_migrations:
            if destination != "head":
                # if the scripts revision is greater than its destination it means it was created on a later date.
                if int(script.revision) > int(destination):
                    logger.debug(
                        f"Skipped revision {script.revision} as its newer than the destination {destination}"
                    )
                    continue

            if max_lookback_days != -1 and current_rev:
                # if the script revision is smaller than the oldest allowed revision skip it.
                if int(script.revision) < int(oldest_allowed_revision):
                    logger.debug(
                        f"Skipped revision {script.revision} as its older than the oldest allowed revision {oldest_allowed_revision}"
                    )
                    continue

            # if we get here no loop-guards have been trigger
            revisions.append(script)

        return [
            migration.MigrationStep.upgrade_from_script(self.revision_map, script)
            for script in revisions
        ]

    def _downgrade_revs(self, destination: str, current_rev: str) -> List[RevisionStep]:
        if destination.startswith("-"):
            steps = self.get_down_revisions_steps(int(destination[1:]))
        else:
            steps = self.get_down_revisions(destination)

        return [
            migration.MigrationStep.downgrade_from_script(
                self.revision_map, self.get_revision(str(step))
            )
            for step in steps
        ]

    def _generate_template(self, src: str, dest: str, **kw: Any) -> None:
        logger.info(f"Generating {os.path.abspath(dest)}")
        util.template_to_file(src, dest, self.output_encoding, **kw)

    def _copy_file(self, src: str, dest: str) -> None:
        logger.info(f"Generating {os.path.abspath(dest)}")
        shutil.copy(src, dest)

    def _ensure_directory(self, path: str) -> None:
        path = os.path.abspath(path)
        if not os.path.exists(path):
            logger.info(f"Creating directory {path}")
            os.makedirs(path)

    @staticmethod
    def from_parent(
        parent: ScriptDirectory, additional_options: dict
    ) -> "SqlScriptDirectory":
        return SqlScriptDirectory(**vars(parent), **additional_options)

    @staticmethod
    def from_config(config, additional_options: dict) -> "SqlScriptDirectory":
        return SqlScriptDirectory.from_parent(
            ScriptDirectory.from_config(config), additional_options
        )

    def __repr__(self):
        return f"<< {self.__class__.__name__ } >>"
