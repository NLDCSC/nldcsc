import os.path
from shutil import rmtree

import mock
import pytest
from sqlalchemy import inspect, select

from nldcsc.flask_plugins.flask_sql_migrate import SqlMigrate


@pytest.fixture()
def app():
    from tests.applications.sql_migrate_app import app

    app.config["TESTING"] = True

    yield app


@pytest.fixture()
def test_dir():
    dirs = [
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "..",
            "migrations",
        )
    ]

    # cleanup before incase some other test does not properly clean the test dirs.
    for dir in dirs:
        if os.path.exists(dir):
            rmtree(dir)

    yield os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")

    for dir in dirs:
        if os.path.exists(dir):
            rmtree(dir)


@pytest.fixture()
def db_handle(app):
    from tests.applications.sql_migrate_app import db

    with app.app_context():
        yield db

        # The test app uses an in memory database. If we close the connection it gets removed.
        db.engine.dispose()


@pytest.fixture
def sql_migrate(app):
    from tests.applications.sql_migrate_app import db

    migrate = SqlMigrate()
    migrate.init_app(app, db)

    with app.app_context():
        yield migrate


class TestSqlMigrate:
    def test_happy_migration_run(self, sql_migrate, test_dir):
        assert not os.path.exists(
            os.path.join(test_dir, sql_migrate.directory)
        ), "Migration directory should not exist!"

        sql_migrate.init()

        assert os.path.exists(
            os.path.join(test_dir, sql_migrate.directory)
        ), "Migration directory should exist!"

        assert (
            len(os.listdir(os.path.join(test_dir, sql_migrate.directory, "versions")))
            == 0
        ), "version dir should be empty!"

        sql_migrate.migrate()

        assert (
            len(
                [
                    f
                    for f in os.listdir(
                        os.path.join(test_dir, sql_migrate.directory, "versions")
                    )
                    if os.path.isfile(
                        os.path.join(test_dir, sql_migrate.directory, "versions", f)
                    )
                ]
            )
            == 1
        ), "1 migration should be present in the migration directory!"

    def test_happy_upgrade_run(self, sql_migrate, app, db_handle, test_dir):
        # this test uses the init and migrate, if that test fails, this one will as well.
        sql_migrate.init()
        sql_migrate.migrate()

        assert not inspect(db_handle.engine).has_table(
            "user"
        ), "user table should not exist!"

        sql_migrate.upgrade()

        assert inspect(db_handle.engine).has_table("user"), "user table should exist!"

    def test_happy_downgrade_run(self, sql_migrate, app, db_handle, test_dir):
        # this test uses the init and migrate, if that test fails, this one will as well.
        sql_migrate.init()
        sql_migrate.migrate()
        sql_migrate.upgrade()

        assert inspect(db_handle.engine).has_table("user"), "user table should exist!"

        sql_migrate.downgrade()

        assert not inspect(db_handle.engine).has_table(
            "user"
        ), "user table should not exist!"

    def test_happy_drop_run(self, sql_migrate, app, db_handle, test_dir):
        sql_migrate.init()
        sql_migrate.migrate()
        sql_migrate.upgrade()

        assert inspect(db_handle.engine).has_table("user"), "user table should exist!"
        assert os.path.exists(
            os.path.join(test_dir, sql_migrate.directory)
        ), "Migration directory should exist!"

        sql_migrate.drop()

        assert not inspect(db_handle.engine).has_table(
            "user"
        ), "user table should not exist!"
        assert not os.path.exists(
            os.path.join(test_dir, sql_migrate.directory)
        ), "Migration directory should not exist!"
