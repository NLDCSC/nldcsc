import logging
import os.path
from shutil import rmtree

import mock
import pytest

from nldcsc.sql_migrations.flask_sql_migrate import FlaskSqlMigrate
from tests.helpers.capture_logging import catch_logs, records_to_tuples


@pytest.fixture
def sql_migrate_object():
    fsm = FlaskSqlMigrate(
        app_ref="migrate_app",
        cwd=os.path.join(os.path.dirname(os.path.realpath(__file__)), "applications"),
    )
    yield fsm


@pytest.fixture()
def app():
    from tests.applications.migrate_app import app

    yield app

    # clean up / reset resources here


@pytest.fixture()
def client(app):
    return app.test_client()


class TestSqlMigrator:
    def test_import(self):
        # needs to be set to True in order to properly check the error response message (without ansi color codes)
        os.environ["GELF_SYSLOG"] = "True"

        fsm = FlaskSqlMigrate()

        assert isinstance(fsm, FlaskSqlMigrate)

        logger_name = "nldcsc.sql_migrations.flask_sql_migrate"
        logger = logging.getLogger(logger_name)
        logger.propagate = True

        # test for 'Error: Could not locate a Flask application... etc etc'
        with catch_logs(level=logging.INFO, logger=logger) as handler:
            fsm.db_init()
            assert records_to_tuples(handler.records) == [
                (
                    logger_name,
                    logging.ERROR,
                    "Error: Could not locate a Flask application. Use the 'flask --app' "
                    "option, 'FLASK_APP' environment variable, or a 'wsgi.py' or 'app.py' "
                    "file in the current directory.\n\nUsage: flask [OPTIONS] COMMAND [ARGS]..."
                    "\nTry 'flask --help' for help.\n\nError: No such command 'db'.\n",
                )
            ]

    @mock.patch("nldcsc.sql_migrations.flask_sql_migrate.os")
    def test_class_init(self, fsm_os):
        # set up the mock
        fsm_os.path.exists.return_value = True
        fsm_os.path.dirname.return_value = "/tmp/test"

        fsm = FlaskSqlMigrate(app_ref="/tmp/test/app.py:app")

        # check if FlaskSqlMigrate called os.path.dirname with the correct application path
        fsm_os.path.dirname.assert_called_with("/tmp/test/app.py")

        del fsm
        # retest with no app name added to path
        fsm = FlaskSqlMigrate(app_ref="/tmp/test/app.py")

        fsm_os.path.dirname.assert_called_with("/tmp/test/app.py")

        del fsm
        # retest with no dirname returning ""
        fsm_os.path.dirname.return_value = ""
        with pytest.raises(ValueError):
            fsm = FlaskSqlMigrate(app_ref="/tmp/test/app.py")
            fsm_os.path.dirname.assert_called_with("/tmp/test/app.py")

        # retest with os.path.exists returns False
        fsm_os.path.exists.return_value = False

        with pytest.raises(FileNotFoundError):
            fsm = FlaskSqlMigrate(app_ref="/tmp/test/app.py")

        with pytest.raises(AttributeError):
            fsm = FlaskSqlMigrate(app_ref="tmp.test.app:app")

        with pytest.raises(FileNotFoundError):
            fsm = FlaskSqlMigrate(app_ref="tmp.test.app:app", cwd="/tmp/test")

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

        sql_migrate_object.db_stamp()

    def test_user_insert(self, app, client):
        from tests.applications.migrate_app import db, User

        user1 = User(username="user1")
        user2 = User(username="user2")

        with app.app_context():
            User.query.delete()
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()

        res = client.get("/")

        assert res.data == b'[{"user":"user1"},{"user":"user2"}]\n'

        # cleanup... should be handled more elegantly... somehow...
        rmtree(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "applications",
                "migrations",
            )
        )
        rmtree(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "instance")
        )
