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

        # cleanup... should be handled more elegantly...
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
