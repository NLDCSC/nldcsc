import os.path
from shutil import rmtree

import pytest


@pytest.fixture
def sql_migrate_object():
    from nldcsc.sql_migrations.flask_sql_migrate import FlaskSqlMigrate

    fsm = FlaskSqlMigrate(
        app_ref="migrate_app",
        cwd=os.path.join(os.path.dirname(os.path.realpath(__file__)), "applications"),
    )
    yield fsm

    rmtree(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "applications", "migrations"
        )
    )
    rmtree(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "instance"))


class TestSqlMigrator:
    def test_import(self):
        from nldcsc.sql_migrations.flask_sql_migrate import FlaskSqlMigrate

        fsm = FlaskSqlMigrate()

        assert isinstance(fsm, FlaskSqlMigrate)

    def test_migration_run(self, sql_migrate_object):

        sql_migrate_object.db_init()

        assert os.path.exists(
            os.path.join(sql_migrate_object.current_dir, "migrations")
        )

        sql_migrate_object.db_migrate()

        assert (
            len(
                os.listdir(
                    os.path.join(
                        sql_migrate_object.current_dir, "migrations", "versions"
                    )
                )
            )
            != 0
        )

        sql_migrate_object.db_update()
