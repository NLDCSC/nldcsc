import logging
import multiprocessing
import os
from pathlib import Path

from flask import Flask
from gunicorn.app.base import BaseApplication

from nldcsc.generic.utils import getenv_bool
from nldcsc.loggers.app_logger import AppLogger
from nldcsc.sql_migrations.flask_sql_migrate import FlaskSqlMigrate

logging.setLoggerClass(AppLogger)


class StandaloneApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


class FlaskAppManager(object):
    def __init__(
        self, version: str, app: Flask, init_sql_database: bool = False, *args, **kwargs
    ):
        self.logger = logging.getLogger(__name__)

        self.logger.info("Initializing FlaskAppManager...")

        self.app = app

        if not isinstance(self.app, Flask):
            raise AttributeError(
                f"The provided app variable is not of type 'Flask' but {type(self.app)}"
            )

        self.version = version
        self.init_sql_database = init_sql_database

        self.max_workers = int(os.getenv("WEB_MAX_WORKERS", 0))
        self.web_worker_timeout = int(os.getenv("WEB_WORKER_TIMEOUT", 60))

        self.web_tls_key_path = os.getenv("WEB_TLS_KEY_PATH", "/app/data/certs/key.pem")
        self.web_tls_cert_path = os.getenv(
            "WEB_TLS_CERT_PATH", "/app/data/certs/cert.pem"
        )

        self.app_working_dir = os.getenv("APP_WORKING_DIR", "/app")

        self.debug = getenv_bool("DEBUG", "False")
        self.debug_with_ssl = getenv_bool("DEBUG_WITH_SSL", "False")

        self.bind_host = os.getenv("BIND_HOST", "localhost")
        self.bind_port = int(os.getenv("BIND_PORT", 5050))

        self.logger.info(
            f"Initialization complete, call the run method to start the app!"
        )

    def run(self):
        self.logger.info("Trying to start the app...")

        try:
            self.logger.info(f"Running version: {self.version}")

            if self.debug:
                if self.debug_with_ssl:
                    self.app.run(
                        host=self.bind_host,
                        port=self.bind_port,
                        ssl_context="adhoc",
                    )
                else:
                    self.app.run(
                        host=self.bind_host,
                        port=self.bind_port,
                    )

            else:
                if self.init_sql_database:
                    if not os.path.exists(
                        os.path.join(self.app_working_dir, "INIT_COMPLETED")
                    ):
                        fsm = FlaskSqlMigrate()

                        if not os.path.exists(
                            os.path.join(self.app_working_dir, "migrations")
                        ):
                            fsm.db_init()

                        fsm.db_migrate()
                        fsm.db_update()

                        try:
                            Path(
                                os.path.join(self.app_working_dir, "INIT_COMPLETED")
                            ).touch()
                        except FileNotFoundError:
                            os.mkdir(os.path.join(self.app_working_dir))
                            Path(
                                os.path.join(self.app_working_dir, "INIT_COMPLETED")
                            ).touch()

                options = {
                    "bind": f"{self.bind_host}:{self.bind_port}",
                    "workers": self._number_of_workers(),
                    "timeout": self.web_worker_timeout,
                    "logger_class": "nldcsc.loggers.gunicorn_logger.GunicornLogger",
                    "access_log_format": "%(t)s src_ip=%(h)s request=%(r)s request_method=%(m)s status=%(s)s "
                    "response_length=%(b)s referrer=%(f)s url=%(U)s query=?%(q)s user_agent=%(a)s t_ms=%(L)s",
                }
                if os.path.exists(self.web_tls_key_path) and os.path.exists(
                    self.web_tls_cert_path
                ):
                    options["keyfile"] = self.web_tls_key_path
                    options["certfile"] = self.web_tls_cert_path
                    StandaloneApplication(self.app, options).run()
                else:
                    # no TLS; assume running behind reverse proxy that handles TLS offloading; switching to plain http
                    StandaloneApplication(self.app, options).run()

        except Exception:
            raise

    def _number_of_workers(self):
        if self.max_workers != 0:
            return self.max_workers
        else:
            return (multiprocessing.cpu_count() * 2) + 1
