import logging
import os.path
from shutil import rmtree

import pytest

from tests.helpers.capture_logging import catch_logs, records_to_tuples


@pytest.fixture
def sql_migrate_object():
    from nldcsc.sql_migrations.flask_sql_migrate import FlaskSqlMigrate

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
        from nldcsc.sql_migrations.flask_sql_migrate import FlaskSqlMigrate

        fsm = FlaskSqlMigrate()

        assert isinstance(fsm, FlaskSqlMigrate)

        logger_name = "nldcsc.sql_migrations.flask_sql_migrate"
        logger = logging.getLogger(logger_name)
        logger.propagate = True

        # test for 'Error: Could not locate a Flask application.'
        with catch_logs(level=logging.INFO, logger=logger) as handler:
            fsm.db_init()
            assert records_to_tuples(handler.records) == [
                (
                    logger_name,
                    logging.ERROR,
                    "Error: Could not locate a Flask application. Use the 'flask --app' "
                    "option, 'FLASK_APP' environment variable, or a 'wsgi.py' or 'app.py' "
                    "file in the current directory.",
                )
            ]

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
