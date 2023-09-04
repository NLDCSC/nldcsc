class TestLogger:
    def test_logger_import(self):
        try:
            from nldcsc.loggers.app_logger import AppLogger
        except ImportError:
            raise
