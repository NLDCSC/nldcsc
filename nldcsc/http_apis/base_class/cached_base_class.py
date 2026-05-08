import logging
from collections import OrderedDict, namedtuple
from contextlib import contextmanager
from contextvars import ContextVar
from functools import partial
from typing import Any, Callable, Concatenate, ParamSpec, TypeVar, Optional
from uuid import uuid4

import urllib3
from requests import JSONDecodeError, Response
from requests.adapters import HTTPAdapter, Retry
from requests_cache import CachedSession
from requests_cache.backends import BaseCache, SQLiteCache

P = ParamSpec("P")
R = TypeVar("R")
C = TypeVar("C")


def signature_of(_: Callable[P, Any]):
    def wrapper(f: Callable[[C], R]) -> Callable[Concatenate[C, P], R]:
        return f

    return wrapper


class CachedAPI:
    methods = namedtuple("methods", ("GET", "POST", "DELETE", "PUT", "PATCH"))(
        "get", "post", "delete", "put", "patch"
    )
    _session_kwargs = ContextVar("session_kwargs")

    def __init__(
        self,
        baseurl: str,
        api_path: Optional[str] = None,
        proxies: Optional[dict[str, str]] = None,
        user_agent: str = "CachedApi",
        verify: bool | str = True,
        timeout: int = 10,
        max_sessions: int = 128,
        persist_self: bool = True,
        default_retry: Optional[Retry] = None,
        default_expiry: int = 3600,
        default_backend: Optional[Callable[[], BaseCache]] = None,
    ):
        self.baseurl = baseurl.removesuffix("/")
        self.api_path = api_path.strip("/") if api_path else None
        self.proxies = proxies
        self.user_agent = user_agent
        self.verify = verify
        self.timeout = timeout
        self.max_sessions = max_sessions
        self.persist = persist_self
        self.default_backend = (
            default_backend
            if default_backend
            else partial(
                SQLiteCache, db_path=f"file:{uuid4()}?mode=memory&cache=shared"
            )
        )
        self.retry = (
            default_retry
            if default_retry
            else Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[500, 502, 503, 504],
            )
        )
        self.default_session_kwargs = {
            "cache_control": True,
            "expire_after": default_expiry,
        }
        self.sessions: OrderedDict[str, CachedSession] = OrderedDict()
        self.headers = self.default_headers
        self.logger = logging.getLogger(self.__class__.__name__)

        if self.verify is False:
            urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)

    @property
    def default_headers(self):
        return {
            "User-Agent": f"{self.user_agent}",
        }

    def set_header(self, key: str, value: str):
        self.headers[key] = value

    def del_header(self, key: str):
        self.headers.pop(key, None)

    def reset_headers(self):
        self.headers = self.default_headers

    def clear_headers(self):
        self.headers = {}

    @contextmanager
    @signature_of(CachedSession)
    def override_session_options(self, **kwargs):
        try:
            t = self._session_kwargs.set(kwargs)
            yield
        finally:
            self._session_kwargs.reset(t)

    def persist_session(self, key: str, session: CachedSession):
        self.logger.debug(f"Persisting session {session=} for {key=}")

        if current := self.sessions.pop(key, None):
            self.logger.debug(f"Closing session {current=} due to replacement")
            current.close()

        self.sessions[key] = session

        if len(self.sessions) > self.max_sessions:
            oldest_key, session = self.sessions.popitem(False)
            self.logger.debug(
                f"Closing session {session=} for {oldest_key=} due to exceeding {self.max_sessions=}"
            )

            session.close()

    @staticmethod
    def create_session_key(backend, **kwargs):
        return f"{backend}:{kwargs}"

    def close(self):
        while self.sessions:
            _, session = self.sessions.popitem()
            session.close()

    def get_session(
        self,
        force_recreate: bool = False,
        allow_persist: bool = True,
        **kwargs,
    ):
        backend: BaseCache = kwargs.pop("backend", self.default_backend())
        kwargs = kwargs or self._session_kwargs.get(self.default_session_kwargs)

        key = self.create_session_key(backend, **kwargs)

        try:
            self.sessions.move_to_end(key)
        except KeyError:
            s = None
        else:
            s = self.sessions.get(key)

        if s and not force_recreate:
            self.logger.debug(f"Reusing existing session {s=}")
            return s

        s = (
            CachedSession(backend=backend, **kwargs)
            if backend
            else CachedSession(**kwargs)
        )

        if self.retry:
            adapter = HTTPAdapter(max_retries=self.retry)

            s.mount("http://", adapter)
            s.mount("https://", adapter)

        s.verify = self.verify
        s.headers.update(self.headers)

        if self.proxies:
            s.proxies.update(self.proxies)

        if self.persist and allow_persist:
            self.persist_session(key, s)

        return s

    def build_url(self, resource: str | None, ignore_api_path: bool = False):
        if resource:
            resource = resource.removeprefix("/")

        url = self.baseurl

        if self.api_path and not ignore_api_path:
            url += f"/{self.api_path}"

        if resource:
            url += f"/{resource}"

        return url

    def __del__(self):
        self.close()

    def call(
        self,
        method: str,
        resource: str = None,
        unpack_response: bool = True,
        ignore_api_path: bool = False,
        allow_persist_session: bool = True,
        force_recreate_session: bool = False,
        **kwargs,
    ):
        if method not in self.methods:
            raise ValueError(f"Unknown {method=}")

        s = self.get_session(
            force_recreate=force_recreate_session, allow_persist=allow_persist_session
        )

        method = getattr(s, method)

        return self.request(
            method,
            self.build_url(resource, ignore_api_path),
            unpack_response,
            **kwargs,
        )

    def unpack_response(self, response: Response):
        if not response.ok:
            response.raise_for_status()

        try:
            return response.json()
        except JSONDecodeError:
            return response.text

    def request(
        self,
        method: Callable[..., Response],
        url: str,
        unpack: bool,
        timeout: int = None,
        **kwargs,
    ):
        if timeout is None:
            timeout = self.timeout

        r = method(url, timeout=timeout, **kwargs)

        if unpack:
            return self.unpack_response(r)
        return r
