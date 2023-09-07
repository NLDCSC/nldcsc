import logging
import os

import mock
from mock.mock import patch

from tests.helpers.capture_logging import catch_logs, records_to_tuples


class TestLogger:
    def test_logger_import(self):
        try:
            from nldcsc.loggers.app_logger import AppLogger

            logging.setLoggerClass(AppLogger)

            logger_name = "TEST"
            logger = logging.getLogger(logger_name)
            logger.propagate = True

            with catch_logs(level=logging.DEBUG, logger=logger) as handler:
                logger.debug("Debug message")
                logger.info("Info message")
                logger.warning("Warning message")
                logger.error("Error message")
                logger.critical("Critical message")
                assert records_to_tuples(handler.records) == [
                    (logger_name, logging.DEBUG, "Debug message"),
                    (logger_name, logging.INFO, "Info message"),
                    (logger_name, logging.WARNING, "Warning message"),
                    (logger_name, logging.ERROR, "Error message"),
                    (logger_name, logging.CRITICAL, "Critical message"),
                ]

        except Exception:
            raise

    def test_handler_types(self):
        os.environ["GELF_SYSLOG"] = "True"

        from nldcsc.loggers.app_logger import AppLogger
        from logging.handlers import RotatingFileHandler
        from nldcsc.loggers.handlers.gelf_handler import DCSCGelfUDPHandler

        logging.setLoggerClass(AppLogger)

        logger = logging.getLogger("test_handler_types")

        assert len(logger.handlers) == 3
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert isinstance(logger.handlers[1], RotatingFileHandler)
        assert isinstance(logger.handlers[2], DCSCGelfUDPHandler)

    def test_syslog_handler(self):
        os.environ["GELF_SYSLOG"] = "False"

        from nldcsc.loggers.app_logger import AppLogger
        from logging.handlers import RotatingFileHandler
        from nldcsc.loggers.handlers.syslog_handler import FullSysLogHandler

        logging.setLoggerClass(AppLogger)

        logger = logging.getLogger("test_syslog_handler")

        assert len(logger.handlers) == 3
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert isinstance(logger.handlers[1], RotatingFileHandler)
        assert isinstance(logger.handlers[2], FullSysLogHandler)

    @mock.patch("nldcsc.loggers.handlers.syslog_handler.socket.socket.sendto")
    def test_syslog_emit(self, sys_socket):
        os.environ["GELF_SYSLOG"] = "False"
        import socket

        from nldcsc.loggers.app_logger import AppLogger

        logging.setLoggerClass(AppLogger)

        logger = logging.getLogger("test_syslog_emit")
        with patch.object(logger.handlers[2], "socktype", socket.SOCK_DGRAM):
            logger.info("Info test")
            sys_socket.assert_called()

        with patch.object(
            logger.handlers[2], "structured_data", {"data": {"k": "v", "k2": "v2"}}
        ):
            with patch.object(logger.handlers[2], "enterprise_id", 1):
                logger.info("Info structured data")
                sys_socket.assert_called()

        with patch.object(
            logger.handlers[2], "structured_data", {"meta": {"k": "v", "k2": "v2"}}
        ):
            logger.info("Info structured data id")
            sys_socket.assert_called()
