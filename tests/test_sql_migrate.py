import os.path
from shutil import rmtree

import mock
import pytest

from nldcsc.flask_plugins.flask_sql_migrate import SqlMigrate


@pytest.fixture()
def app():
    from tests.applications.sql_migrate_app import app

    app.config["TESTING"] = True

    yield app


@pytest.fixture()
def test_dir():
    yield os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")

    rmtree(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "..",
            "migrations",
        )
    )


@pytest.fixture()
def db_handle(app):
    from tests.applications.sql_migrate_app import db

    with app.app_context():
        yield db

        db.drop_all()


@pytest.fixture
def sql_migrate(app):
    from tests.applications.sql_migrate_app import db

    migrate = SqlMigrate()
    migrate.init_app(app, db)

    with app.app_context():
        yield migrate


class TestSqlMigrate:
    def test_migration_run(self, sql_migrate, test_dir):

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

    def test_upgrade_run(self):
        # this test uses the init and migrate, if that test fails, this one will as well.
        pass

    def test_downgrade_run(self):
        pass

    def test_drop_run(self):
        pass
