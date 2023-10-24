import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import colors

from nldcsc.generic.utils import getenv_bool, getenv_dict
from nldcsc.loggers.formatters.task_formatter import DCSCTaskFormatter
from nldcsc.loggers.handlers.gelf_handler import DCSCGelfUDPHandler
from nldcsc.loggers.handlers.syslog_handler import FullSysLogHandler

CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

level_map = {
    "debug": "magenta",
    "info": "white",
    "warning": "yellow",
    "error": "red",
    "critical": "red",
}


class AppLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        self.formatter = DCSCTaskFormatter(
            "%(asctime)s - %(task_name)s - %(name)-8s - %(levelname)-8s - [%(task_id)s] %(message)s"
        )

        root = logging.getLogger()

        root.setLevel(os.getenv("LOG_LEVEL", "INFO"))

        root_null_handler = logging.NullHandler()
        root.handlers.clear()
        root.addHandler(root_null_handler)

        super().__init__(name, level)

        self.propagate = False

        cli = logging.StreamHandler(stream=sys.stdout)
        cli.setFormatter(self.formatter)
        cli.setLevel(os.getenv("LOG_LEVEL", "INFO"))
        self.addHandler(cli)

        log_file_path = os.getenv("LOG_FILE_PATH", "")

        if log_file_path != "":
            if not os.path.exists(log_file_path):
                os.makedirs(log_file_path)

            crf = RotatingFileHandler(
                filename=os.path.join(
                    log_file_path,
                    os.getenv("LOG_FILE_NAME", "app.log"),
                ),
                maxBytes=100000000,
                backupCount=5,
            )
            crf.setLevel(logging.DEBUG)
            crf.setFormatter(self.formatter)
            self.addHandler(crf)

        if getenv_bool("SYSLOG_ENABLE", "False"):
            syslog_server = os.getenv("SYSLOG_SERVER", "127.0.0.1")
            syslog_port = int(os.getenv("SYSLOG_PORT", 5140))

            if getenv_bool("GELF_SYSLOG", "True"):
                syslog = DCSCGelfUDPHandler(
                    host=syslog_server,
                    port=syslog_port,
                    _application_name=os.getenv("APP_NAME", "YADA"),
                    include_extra_fields=True,
                    debug=True,
                    **getenv_dict("GELF_SYSLOG_ADDITIONAL_FIELDS", None)
                    if getenv_dict("GELF_SYSLOG_ADDITIONAL_FIELDS", None) is not None
                    else {}
                )
            else:
                syslog = FullSysLogHandler(
                    address=(syslog_server, syslog_port),
                    facility=FullSysLogHandler.LOG_LOCAL0,
                    appname=os.getenv("APP_NAME", "YADA"),
                )

            syslog.setFormatter(self.formatter)
            syslog.setLevel(logging.DEBUG)
            self.addHandler(syslog)

    def debug(self, msg, *args, **kwargs):
        """
        Log ‘msg % args’ with severity ‘DEBUG’ and color *MAGENTA.

        To pass exception information, use the keyword argument exc_info with a true value, e.g.

        logger.debug(“Houston, we have a %s”, “thorny problem”, exc_info=1)

        :param msg: Message to log
        :type msg: str
        """

        msg = colors.color("{}".format(msg), fg=level_map["debug"])

        if self.isEnabledFor(DEBUG):
            self._log(DEBUG, msg, args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """
        Log ‘msg % args’ with severity ‘INFO’ and color *WHITE*.

        To pass exception information, use the keyword argument exc_info with a true value, e.g.

        logger.info(“Houston, we have a %s”, “interesting problem”, exc_info=1)

        :param msg: Message to log
        :type msg: str
        """

        msg = colors.color("{}".format(msg), fg=level_map["info"])

        if self.isEnabledFor(INFO):
            self._log(INFO, msg, args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """
        Log ‘msg % args’ with severity ‘WARNING’ and color *YELLOW*.

        To pass exception information, use the keyword argument exc_info with a true value, e.g.

        logger.warning(“Houston, we have a %s”, “bit of a problem”, exc_info=1)

        :param msg: Message to log
        :type msg: str
        """

        msg = colors.color("{}".format(msg), fg=level_map["warning"])

        if self.isEnabledFor(WARNING):
            self._log(WARNING, msg, args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """
        Log ‘msg % args’ with severity ‘ERROR’ and color *RED*.

        Store logged message to the database for dashboard alerting.

        To pass exception information, use the keyword argument exc_info with a true value, e.g.

        logger.error(“Houston, we have a %s”, “major problem”, exc_info=1)

        :param msg: Message to log
        :type msg: str
        """

        msg = colors.color("{}".format(msg), fg=level_map["error"])

        if self.isEnabledFor(ERROR):
            self._log(ERROR, msg, args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """
        Log ‘msg % args’ with severity ‘CRITICAL’ and color *RED*.

        Store logged message to the database for dashboard alerting.

        To pass exception information, use the keyword argument exc_info with a true value, e.g.

        logger.critical(“Houston, we have a %s”, “hell of a problem”, exc_info=1)

        :param msg: Message to log
        :type msg: str
        """

        msg = colors.color("{}".format(msg), fg=level_map["critical"])

        if self.isEnabledFor(CRITICAL):
            self._log(CRITICAL, msg, args, **kwargs)
