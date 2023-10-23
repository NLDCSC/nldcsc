import logging
import time
from datetime import datetime

import colors
import rfc3339 as rfc3339
from flask import g
from flask_http_middleware import BaseHTTPMiddleware

from nldcsc.loggers.app_logger import AppLogger

logging.setLoggerClass(AppLogger)


class DebugLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        super().__init__()

    def dispatch(self, request, call_next):
        # before_request
        g.start = time.time()

        response = call_next(request)

        # after_request
        now = time.time()
        duration = round(now - g.start, 2)
        dt = datetime.fromtimestamp(now)
        timestamp = rfc3339.rfc3339(dt, utc=True)

        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        host = request.host.split(":", 1)[0]
        args = dict(request.args)

        log_params = [
            ("method", request.method, "blue"),
            ("path", request.path, "blue"),
            ("status", response.status, "yellow"),
            ("duration", duration, "green"),
            ("time", timestamp, "magenta"),
            ("ip", ip, "gray"),
            ("host", host, "gray"),
            ("params", args, "blue"),
        ]

        request_id = request.headers.get("X-Request-ID")
        if request_id:
            log_params.append(("request_id", request_id, "yellow"))

        parts = []
        for name, value, color in log_params:
            part = colors.color("{}={}".format(name, value), fg=color)
            parts.append(part)
        line = " ".join(parts)

        self.logger.info(line)

        return response
