import os
import logging
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
        from nldcsc.loggers.app_logger import AppLogger
        from logging.handlers import RotatingFileHandler
        from nldcsc.loggers.handlers.gelf_handler import DCSCGelfUDPHandler

        logging.setLoggerClass(AppLogger)

        logger = logging.getLogger("TEST")

        assert len(logger.handlers) == 3
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert isinstance(logger.handlers[1], RotatingFileHandler)
        assert isinstance(logger.handlers[2], DCSCGelfUDPHandler)

    def test_syslog_hander(self):
        from nldcsc.loggers.app_logger import AppLogger
        from logging.handlers import RotatingFileHandler
        from nldcsc.loggers.handlers.syslog_handler import FullSysLogHandler

        os.environ["GELF_SYSLOG"] = "False"

        logging.setLoggerClass(AppLogger)

        logger = logging.getLogger("TEST")

        assert len(logger.handlers) == 3
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert isinstance(logger.handlers[1], RotatingFileHandler)
        assert isinstance(logger.handlers[2], FullSysLogHandler)
