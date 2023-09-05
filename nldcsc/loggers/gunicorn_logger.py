import logging
import os
import sys
from logging.config import fileConfig, dictConfig

import gunicorn.glogging
from gunicorn.glogging import CONFIG_DEFAULTS


class GunicornLogger(gunicorn.glogging.Logger):
    def __init__(self, cfg):
        super().__init__(cfg)

    def setup(self, cfg):
        self.loglevel = self.LOG_LEVELS.get(cfg.loglevel.lower(), logging.INFO)
        self.error_log.setLevel(self.loglevel)
        self.access_log.setLevel(logging.INFO)

        # set gunicorn.error handler
        if self.cfg.capture_output and cfg.errorlog != "-":
            for stream in sys.stdout, sys.stderr:
                stream.flush()

            self.logfile = open(cfg.errorlog, "a+")
            os.dup2(self.logfile.fileno(), sys.stdout.fileno())
            os.dup2(self.logfile.fileno(), sys.stderr.fileno())

        # [DCSC] Force gunicorn to produce an access log; without pushing this to stdout from this instance
        self.cfg.set("accesslog", "Y")

        # [DCSC] Removed error log handler from this instance
        # self._set_handler(
        #     self.error_log,
        #     cfg.errorlog,
        #     logging.Formatter(self.error_fmt, self.datefmt),
        # )

        # [DCSC] Removed stdout accesslog handler
        # set gunicorn.access handler
        # if cfg.accesslog is not None:
        #     self._set_handler(
        #         self.access_log,
        #         cfg.accesslog,
        #         fmt=logging.Formatter(self.access_fmt),
        #         stream=sys.stdout,
        #     )

        # [DCSC] Removed syslog handler
        # set syslog handler
        # if cfg.syslog:
        #     self._set_syslog_handler(self.error_log, cfg, self.syslog_fmt, "error")
        #     if not cfg.disable_redirect_access_to_syslog:
        #         self._set_syslog_handler(
        #             self.access_log, cfg, self.syslog_fmt, "access"
        #         )

        if cfg.logconfig_dict:
            config = CONFIG_DEFAULTS.copy()
            config.update(cfg.logconfig_dict)
            try:
                dictConfig(config)
            except (AttributeError, ImportError, ValueError, TypeError) as exc:
                raise RuntimeError(str(exc))
        elif cfg.logconfig:
            if os.path.exists(cfg.logconfig):
                defaults = CONFIG_DEFAULTS.copy()
                defaults["__file__"] = cfg.logconfig
                defaults["here"] = os.path.dirname(cfg.logconfig)
                fileConfig(
                    cfg.logconfig, defaults=defaults, disable_existing_loggers=False
                )
            else:
                msg = "Error: log config '%s' not found"
                raise RuntimeError(msg % cfg.logconfig)
