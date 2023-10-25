import logging
from abc import ABC, abstractmethod

from flask import Response, Flask

from nldcsc.loggers.app_logger import AppLogger

logging.setLoggerClass(AppLogger)


class BaseHTTPMiddleware(ABC):
    def __init__(self, app: Flask):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.app = app

        @app.before_request
        def before_request():
            return self._before_request()

        @app.after_request
        def after_request(response: Response) -> Response:
            return self._after_request(response)

    @abstractmethod
    def _before_request(self):
        raise NotImplementedError

    @abstractmethod
    def _after_request(self, response: Response) -> Response:
        raise NotImplementedError

    def __repr__(self):
        return f"<< {self.__class__.__name__} >>"
