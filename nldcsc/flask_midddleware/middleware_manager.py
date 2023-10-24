import logging
from typing import List, Tuple

from flask import Flask

from nldcsc.flask_midddleware.base import BaseHTTPMiddleware
from nldcsc.loggers.app_logger import AppLogger

logging.setLoggerClass(AppLogger)


class MiddlewareManager(object):
    def __init__(self, app: Flask = None):
        self.app = app
        self._middleware_stack = {}
        self.logger = logging.getLogger(self.__class__.__name__)

        if self.app is not None:
            self.init_app(app=app)

    @property
    def middleware_stack(self) -> List[Tuple[int, dict]]:
        return sorted(self._middleware_stack.items(), reverse=True)

    def add_middleware(self, middleware_class: type, rank: int, **options):
        """

        Args:
            middleware_class: middleware class
            rank: middleware prority; lower numbered ranks are preferred over higher numbered ranks
            **options: options for the middleware class initialization

        Returns:

        """
        if BaseHTTPMiddleware.__subclasscheck__(middleware_class):
            self._middleware_stack[rank] = {"cls": middleware_class, "options": options}
        else:
            raise Exception(
                "Error Middleware Class : not inherited from BaseHTTPMiddleware class"
            )

    def init_app(self, app: Flask):
        for mw_entry in self.middleware_stack:
            rank, mw = mw_entry
            # init the middleware
            mw["cls"](**mw["options"])

        app.middleware_manager = self

    def __repr__(self):
        return "<< MiddlewareManager >>"
