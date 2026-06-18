from functools import wraps
import os
import re

from eswrap import EsWrap

from nldcsc.generic.utils import getenv_list, getenv_dict

_COMPAT_MIMETYPE_RE = re.compile(
    r"application/(?:vnd\.elasticsearch\+)?(json|x-ndjson|vnd\.mapbox-vector-tile)"
    r"(?:\s*;\s*compatible-with=\d+)?"
)


class FlaskEsWrap(object):
    def __init__(self, app=None, init_standalone: bool = False, **kwargs):
        if app and init_standalone:
            raise Exception("App must be None when 'init_standalone' is set to True")

        self._es = None
        self.kwargs = kwargs

        self.elastic_user = os.getenv("ELASTIC_USER", None)
        self.elastic_password = os.getenv("ELASTIC_PASSWORD", None)

        # Single Elastic connection details
        self.elastic_host = os.getenv("ELASTIC_HOST", "localhost")
        self.elastic_port = int(os.getenv("ELASTIC_PORT", 9200))
        self.elastic_scheme = os.getenv("ELASTIC_SCHEME", "http")

        self.elastic_compat = os.getenv("ELASTIC_COMPAT_VERSION", None)
        # Or as a list[str] | list[dict], takes preference over Single elastic connection details settings
        # When using this option Authentication should be a part of the connection strings,
        # e.g. http://elastic:changeme@localhost:9200/
        self.elastic_connection_details = getenv_list(
            "ELASTIC_CONNECTION_DETAILS", None
        )
        self.elastic_kwargs = getenv_dict("ELASTIC_KWARGS", None)

        if app is not None or init_standalone:
            self.init_app(app)

    def apply_compat_with(self, client: EsWrap):
        transport = client.es_client.transport

        if "perform_request" in transport.__dict__:
            return client

        sub = rf"application/vnd.elasticsearch+\g<1>; compatible-with={self.elastic_compat}"
        original_perform_request = transport.perform_request

        @wraps(original_perform_request)
        def perform_request(*args, **kwargs):  # type: ignore[no-untyped-def]
            headers = kwargs.get("headers")
            if not headers:
                return original_perform_request(*args, **kwargs)

            merged = dict(headers)
            for key in list(merged):
                if key.lower() in ("accept", "content-type") and merged[key]:
                    merged[key] = _COMPAT_MIMETYPE_RE.sub(sub, merged[key])
            kwargs["headers"] = merged
            return original_perform_request(*args, **kwargs)

        setattr(transport, "perform_request", perform_request)

    def init_app(self, app, **kwargs):
        self.kwargs.update(kwargs)

        if self.elastic_kwargs is not None:
            self.kwargs.update(self.elastic_kwargs)

        if len(self.elastic_connection_details) != 0:
            if self.elastic_user is not None and self.elastic_password is not None:
                self._es = EsWrap(
                    connection_details=self.elastic_connection_details,
                    http_auth=(self.elastic_user, self.elastic_password),
                    **self.kwargs if self.kwargs is not None else {},
                )
            else:
                self._es = EsWrap(
                    connection_details=self.elastic_connection_details,
                    **self.kwargs if self.kwargs is not None else {},
                )
        else:
            if self.elastic_user is not None and self.elastic_password is not None:
                self._es = EsWrap(
                    host=self.elastic_host,
                    port=self.elastic_port,
                    scheme=self.elastic_scheme,
                    http_auth=(
                        self.elastic_user,
                        self.elastic_password,
                    ),
                    **self.kwargs if self.kwargs is not None else {},
                )
            else:
                self._es = EsWrap(
                    host=self.elastic_host,
                    port=self.elastic_port,
                    scheme=self.elastic_scheme,
                    **self.kwargs if self.kwargs is not None else {},
                )

        if app is not None:
            app.flask_eswrap = self

        if self.elastic_compat:
            self.apply_compat_with(self._es)

    @property
    def es(self) -> EsWrap:
        return self._es

    def __del__(self):
        del self._es

    def __repr__(self):
        return f"<< FlaskEsWrap >>"
