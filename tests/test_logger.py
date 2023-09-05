class TestLogger:
    def test_logger_import(self):
        try:
            import logging
            from nldcsc.loggers.app_logger import AppLogger

            logging.setLoggerClass(AppLogger)

            logger = logging.getLogger("TEST")

            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")

        except Exception:
            raise

    def test_handler_types(self):
        import logging
        from nldcsc.loggers.app_logger import AppLogger
        from logging.handlers import RotatingFileHandler
        from nldcsc.loggers.handlers.gelf_handler import DCSCGelfUDPHandler

        logging.setLoggerClass(AppLogger)

        logger = logging.getLogger("TEST")

        assert len(logger.handlers) == 3
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert isinstance(logger.handlers[1], RotatingFileHandler)
        assert isinstance(logger.handlers[2], DCSCGelfUDPHandler)
