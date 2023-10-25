import time
from datetime import datetime

import colors
import rfc3339
from flask import g, request, Flask

from nldcsc.flask_midddleware.base import BaseHTTPMiddleware, Response


class DebugLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Flask):
        super().__init__(app=app)

    def _before_request(self):
        g.start = time.time()

    def _after_request(self, response: Response):
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
