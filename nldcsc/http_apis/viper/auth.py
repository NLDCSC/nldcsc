import time
from dataclasses import dataclass
from functools import wraps
from threading import RLock
from typing import Callable

from requests import HTTPError
from requests.auth import AuthBase


from .collections.auth.objects import AuthResponse
from .objects import ErrorItem


@dataclass
class AuthInfo:
    username: str | None = None
    password: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    access_expiry: int = 0
    refresh_expiry: int = 0
    last_updated: int = 0

    def update_with_response(self, response: AuthResponse):
        self.access_token = response.access_token
        self.access_expiry = response.expires_in
        self.refresh_token = response.refresh_token
        self.refresh_expiry = response.refresh_expires_in
        self.last_updated = int(time.time())

    def valid(self):
        return self.access_expiry + self.last_updated - int(time.time()) > 0

    def refresh_valid(self):
        return self.refresh_expiry + self.last_updated - int(time.time()) > 0


class ViperAuth(AuthBase):
    def __init__(
        self,
        auth: tuple[str, str],
        login: Callable[[str, str], AuthResponse],
        refresh: Callable[[str], AuthResponse],
    ):
        super().__init__()
        self._lock = RLock()
        self._recursion_guard = False
        self.auth_info = AuthInfo(*auth)
        self.login = login
        self.refresh = refresh

    def auth_wrap(self, f):
        """
        Wraps a function to automatically retry in case of a 401 and inject this auth class in.

        This wrapper should be applied to a function which accepts either auth as kwarg or passes the kwarg to a request.

        Args:
            f (Callable): callable which accepts or passes the auth
        """
        if hasattr(f, "_auth_wrapped"):
            return f

        @wraps(f)
        def wrapper(*args, **kwargs):
            kwargs.setdefault("auth", self)

            try:
                return f(*args, **kwargs)
            except HTTPError as e:
                if e.response.status_code != 401:
                    raise

                try:
                    error = ErrorItem.from_json(e.response.text)
                except Exception:
                    raise e

                if error.error.code != "TOKEN_FAILURE":
                    raise e

            self.update_token(True)

            return f(*args, **kwargs)

        wrapper._auth_wrapped = True

        return wrapper

    def update_token(self, force: bool = False):
        with self._lock:
            if self.auth_info.valid() and not force:
                return

            if self._recursion_guard:
                return

            self._recursion_guard = True

            try:
                if not self.auth_info.refresh_valid():
                    raise ValueError

                self.auth_info.update_with_response(
                    self.refresh(refresh_token=self.auth_info.refresh_token)
                )
            except (ValueError, HTTPError) as e:
                if isinstance(e, ValueError) or e.response.status_code == 401:
                    self.auth_info.update_with_response(
                        self.login(
                            username=self.auth_info.username,
                            password=self.auth_info.password,
                        )
                    )
                else:
                    raise
            finally:
                self._recursion_guard = False

    def __call__(self, r):
        if not self.auth_info.valid():
            self.update_token()

        r.headers["Authorization"] = f"Bearer {self.auth_info.access_token}"

        return r
