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
        **requests_kwargs,
    ):
        """
        API class which utilizes requests_cache to cache requests.

        By default this class respects the cache control headers; this can be overriden
        by setting the default session kwargs or using the override_session_options context manager when calling your resource.

        When extending this class you probably should call self.call, which is responsible for orchestrating the requests call; see call tree below.

        self.call
            -> self.build_url
            -> self.get_session
                -> self.persist_session
            -> self.request
                -> self.unpack_response

        Args:
            baseurl (str): baseurl of the api resource.
            api_path (Optional[str], optional): api path of the resource. Defaults to None.
            proxies (Optional[dict[str, str]], optional): proxies to use. Defaults to None.
            user_agent (str, optional): user agent to use. Defaults to "CachedApi".
            verify (bool | str, optional): certificate verification, when passing a string it should be a path to the certificate. Defaults to True.
            timeout (int, optional): default timeout to use. Defaults to 10.
            max_sessions (int, optional): max amount of unique sessions this object may create and manage. Defaults to 128.
            persist_self (bool, optional): allow reusing sessions this object creates. Defaults to True.
            default_retry (Optional[Retry], optional): default retry to use. Defaults to 3 retries; bf 1; status 50[0234].
            default_expiry (int, optional): default cache expiry. Defaults to 3600.
            default_backend (Optional[Callable[[], BaseCache]], optional): default cache backend to use. Defaults to an in memory SQLiteCache.

        Kwargs
            **requests_kwargs (Any, optional): Kwargs to pass to every requests created like authentication headers.

        """
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
        self.requests_kwargs = requests_kwargs
        self.sessions: OrderedDict[str, CachedSession] = OrderedDict()
        self.headers = self.default_headers
        self.logger = logging.getLogger(self.__class__.__name__)

        if self.verify is False:
            urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)

    @property
    def default_headers(self):
        """
        Default headers of this class.

        Returns:
            dict: dict containing http headers
        """
        return {
            "User-Agent": f"{self.user_agent}",
        }

    def set_header(self, key: str, value: str):
        """
        Set a header key to a value.

        Args:
            key (str): http header to set.
            value (str): value of http header.
        """
        self.headers[key] = value

    def del_header(self, key: str):
        """
        Remove a header.

        Args:
            key (str): http header to remove.
        """
        self.headers.pop(key, None)

    def reset_headers(self):
        """
        Reset headers to the default defined in default_headers.
        """
        self.headers = self.default_headers

    def clear_headers(self):
        """
        Clear all headers.
        """
        self.headers = {}

    @contextmanager
    @signature_of(CachedSession)
    def override_session_options(self, **kwargs):
        """
        Context manager to override the default kwargs handed to create or fetch a CachedSession.
        """
        try:
            t = self._session_kwargs.set(kwargs)
            yield
        finally:
            self._session_kwargs.reset(t)

    def persist_session(self, key: str, session: CachedSession):
        """
        Persist a session to this objects session store.

        Evicts existing sessions (lru) if max_sessions is exceeded.

        Args:
            key (str): session key.
            session (CachedSession): session to store.
        """
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
        """
        Creates a unique key that describes a session and its kwargs.

        The unique consists of the backend settings and session kwargs.

        Args:
            backend (BaseCache): backend cache that is used.

        Returns:
            str: unique key describing this session
        """

        return f"{backend}:{kwargs}"

    def close(self):
        """
        Close and evict all sessions managed by this object.
        """
        while self.sessions:
            _, session = self.sessions.popitem()
            session.close()

    def update_session(self, session: CachedSession):
        """
        Updates session to contain the latest settings.

        Args:
            session (CachedSession): session to

        Returns:
            CachedSession: Updated session
        """
        session.verify = self.verify

        if self.proxies:
            session.proxies.update(self.proxies)

        return session

    def get_session(
        self,
        force_recreate: bool = False,
        allow_persist: bool = True,
        **kwargs,
    ):
        """
        Create or get an existing session from the session store.

        Args:
            force_recreate (bool, optional): force recreating the session skipping the session store. Defaults to False.
            allow_persist (bool, optional): allow saving a session to the session store if newly created. Defaults to True.

        Kwargs:
            **kwargs: Kwargs to this function will override the default session kwargs and the kwargs set when using the override_session_options context manager

        Returns:
            CachedSession: a cached session instance.
        """
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

            return self.update_session(s)
        elif s:
            s.close()

        s = (
            CachedSession(backend=backend, **kwargs)
            if backend
            else CachedSession(**kwargs)
        )

        if self.retry:
            adapter = HTTPAdapter(max_retries=self.retry)

            s.mount("http://", adapter)
            s.mount("https://", adapter)

        if self.persist and allow_persist:
            self.persist_session(key, s)

        return self.update_session(s)

    def build_url(self, resource: str | None, ignore_api_path: bool = False):
        """
        Build a resource url using the baseurl, api path and resource.

        Args:
            resource (str | None): resource to create an url for.
            ignore_api_path (bool, optional): ignore the default api path set. Defaults to False.

        Returns:
            str: complete api path to call.
        """
        if resource:
            resource = resource.removeprefix("/")

        url = self.baseurl

        if self.api_path and not ignore_api_path:
            url += f"/{self.api_path}"

        if resource:
            url += f"/{resource}"

        return url

    def __del__(self):
        """
        Attempts to close all existing session when this object is deleted.
        """
        if hasattr(self, "sessions"):
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
        """
        Call an endpoint.

        This function should be the default entrypoint when calling a resource. As it will orchestrate the correct flow to call the resource; see call tree below.

        self.call
            -> self.build_url
            -> self.get_session
                -> self.persist_session
            -> self.request
                -> self.unpack_response

        Args:
            method (str): http method to use.
            resource (str, optional): resource to call. Defaults to None.
            unpack_response (bool, optional): if the response should be unpacked or returned as Response. Defaults to True.
            ignore_api_path (bool, optional): if the default api path should be ignored. Defaults to False.
            allow_persist_session (bool, optional): allow the created session to be persisted. Defaults to True.
            force_recreate_session (bool, optional): force the session to be recreated. Defaults to False.

        Kwargs:
            **kwargs: additional kwargs to pass to the request call.

        Raises:
            ValueError: If the http method passed is unknown.

        Returns:
            dict | list | str | Response: Depending if unpack_response is set and the type of data returned from the api.
        """

        if method not in self.methods:
            raise ValueError(f"Unknown {method=}")

        s = self.get_session(
            force_recreate=force_recreate_session, allow_persist=allow_persist_session
        )

        method = getattr(s, method)

        requests_kwargs = {**self.requests_kwargs, **kwargs}
        requests_kwargs["headers"] = {
            **requests_kwargs.get("headers", {}),
            **self.headers,
        }

        try:
            response = self.request(
                method,
                self.build_url(resource, ignore_api_path),
                unpack_response,
                **requests_kwargs,
            )
        finally:
            if not self.persist or not allow_persist_session:
                s.close()
        return response

    def unpack_response(self, response: Response):
        """
        Unpacks a response object to by decoding it as JSON or raw text.

        Args:
            response (Response): response to unpack.

        Returns:
            dict | list | str: Depends of the type of data returned.
        """
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
        """
        Send the actual request by calling the function provided on the session or requests object.

        Args:
            method (Callable[..., Response]): requests function to call.
            url (str): url to pass to requests.
            unpack (bool): if the response should be unpacked.
            timeout (int, optional): overriding timeout otherwise the default timeout is used. Defaults to None.

        Returns:
            dict | list | str | Response: Depending if unpack_response is set and the type of data returned from the api.
        """
        if timeout is None:
            timeout = self.timeout

        r = method(url, timeout=timeout, **kwargs)

        if unpack:
            return self.unpack_response(r)
        return r
