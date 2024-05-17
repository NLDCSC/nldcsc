import logging
import multiprocessing
import os
from pathlib import Path

from flask import Flask
from flask_socketio import SocketIO
from gunicorn.app.base import BaseApplication
from nldcsc.generic.utils import getenv_bool
from nldcsc.loggers.app_logger import AppLogger
from nldcsc.sql_migrations.flask_sql_migrate import FlaskSqlMigrate

logging.setLoggerClass(AppLogger)


class StandaloneApplication(BaseApplication):
    """
    An application interface for configuring a WSGI application to run with gunicorn.
    """

    def __init__(self, app, options=None) -> None:
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self) -> None:
        """
        Method for loading the proper options into the gunicorn configuration.
        """
        config: dict = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        """
        method that returns the configured WSGI application.
        """
        return self.application


class FlaskAppManager(object):
    """
    An app manager class for configuring and running a flask application
    """

    def __init__(
        self,
        version: str,
        app: Flask,
        socketio: SocketIO = None,
        init_sql_database: bool = False,
        **kwargs,
    ) -> None:
        """
        Initialize a new FlaskAppManager instance.

        Args:
            version: version of the application
            app: Flask application
            socketio: Flask-SocketIO instance
            init_sql_database: Whether to initialize the database
            **kwargs: additional keyword arguments that will be passed to the webserver options dictionary
        """

        self.logger = logging.getLogger(__name__)

        self.logger.info("Initializing FlaskAppManager...")

        self.app = app
        self.socketio = socketio

        if not isinstance(self.app, Flask):
            raise AttributeError(
                f"The provided app variable is not of type 'Flask' but {type(self.app)}"
            )

        self.version: str = version
        self.init_sql_database: bool = init_sql_database

        self.worker_class: str = os.getenv("WEB_WORKER_CLASS", "sync")
        self.max_workers: int = int(os.getenv("WEB_MAX_WORKERS", 0))
        self.web_worker_timeout: int = int(os.getenv("WEB_WORKER_TIMEOUT", 60))

        self.web_tls_key_path: str = os.getenv(
            "WEB_TLS_KEY_PATH", "/app/data/certs/key.pem"
        )
        self.web_tls_cert_path: str = os.getenv(
            "WEB_TLS_CERT_PATH", "/app/data/certs/cert.pem"
        )

        self.app_working_dir: str = os.getenv("APP_WORKING_DIR", "/app")

        self.debug: bool = getenv_bool("DEBUG", "False")
        self.debug_with_ssl: bool = getenv_bool("DEBUG_WITH_SSL", "False")

        self.bind_host: str = os.getenv("BIND_HOST", "localhost")
        self.bind_port: int = int(os.getenv("BIND_PORT", 5050))

        self.kwargs = kwargs

        self.logger.info(
            "Initialization complete, call the run method to start the app!"
        )

    def run(self) -> None:
        """
        Runs the application

        The application will start using gunicorn, if debug is disabled. Otherwise, it will use the flask development
        server.
        """
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
                        fsm = FlaskSqlMigrate(
                            cwd=self.app.instance_path.rstrip("/instance"),
                            app_ref=self.app.import_name,
                        )

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
                if self.socketio is None:
                    if self.worker_class not in ["sync", "eventlet", "gevent"]:
                        raise ValueError(
                            f"Unsupported worker_class {self.worker_class} detected!"
                        )

                    options = {
                        "bind": f"{self.bind_host}:{self.bind_port}",
                        "workers": self._number_of_workers(),
                        "timeout": self.web_worker_timeout,
                        "worker_class": self.worker_class,
                        "logger_class": "nldcsc.loggers.gunicorn_logger.GunicornLogger",
                        "access_log_format": "%(t)s src_ip=%(h)s request=%(r)s request_method=%(m)s status=%(s)s "
                        "response_length=%(b)s referrer=%(f)s url=%(U)s query=?%(q)s user_agent=%(a)s t_ms=%(L)s",
                    }

                    options.update(self.kwargs)

                    if os.path.exists(self.web_tls_key_path) and os.path.exists(
                        self.web_tls_cert_path
                    ):
                        options["keyfile"] = self.web_tls_key_path
                        options["certfile"] = self.web_tls_cert_path
                        StandaloneApplication(self.app, options).run()
                    else:
                        # no TLS; assume running behind reverse proxy that handles TLS offloading; switching to
                        # plain http
                        StandaloneApplication(self.app, options).run()
                else:
                    options = {"log_output": True}

                    options.update(self.kwargs)

                    if os.path.exists(self.web_tls_key_path) and os.path.exists(
                        self.web_tls_cert_path
                    ):
                        options["keyfile"] = self.web_tls_key_path
                        options["certfile"] = self.web_tls_cert_path
                        self.socketio.run(
                            app=self.app,
                            host=self.bind_host,
                            port=self.bind_port,
                            **options,
                        )
                    else:
                        # Socketio app
                        # no TLS; assume running behind reverse proxy that handles TLS offloading; switching to
                        # plain http
                        self.socketio.run(
                            app=self.app,
                            host=self.bind_host,
                            port=self.bind_port,
                            **options,
                        )
        except Exception:
            raise

    def _number_of_workers(self) -> int:
        """
        returns number of workers to use.

        number of workers will be based on the configured value or defaults to '(cpu_count * 2) + 1' if nothing is
        configured.

        Returns:
            int: number of workers to use
        """
        if self.max_workers != 0:
            return self.max_workers
        else:
            return (multiprocessing.cpu_count() * 2) + 1
