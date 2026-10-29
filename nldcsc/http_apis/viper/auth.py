import time
from dataclasses import dataclass
from functools import wraps
from math import isfinite
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
    access_expiry: float = 0
    refresh_expiry: float = 0
    last_updated: float = 0

    def update_with_response(self, response: AuthResponse, requested_at=None):
        access_expiry = float(response.expires_in)
        refresh_expiry = float(response.refresh_expires_in)

        if (
            not isinstance(response.access_token, str)
            or not response.access_token
            or not isinstance(response.refresh_token, str)
            or not response.refresh_token
            or not isfinite(access_expiry)
            or access_expiry <= 0
            or not isfinite(refresh_expiry)
            or refresh_expiry < 0
        ):
            raise ValueError("Invalid Viper token response.")

        self.access_token = response.access_token
        self.refresh_token = response.refresh_token
        self.access_expiry = access_expiry
        self.refresh_expiry = refresh_expiry
        # Response latency must not extend the token's lifetime.
        self.last_updated = time.monotonic() if requested_at is None else requested_at

    def access_valid(self):
        return (
            bool(self.access_token)
            and time.monotonic() < self.last_updated + self.access_expiry
        )

    def valid(self):
        margin = min(30, self.access_expiry / 2)
        return (
            bool(self.access_token)
            and time.monotonic() < self.last_updated + self.access_expiry - margin
        )

    def refresh_valid(self):
        return (
            bool(self.refresh_token)
            and time.monotonic() < self.last_updated + self.refresh_expiry
        )


class ViperTokenRenewed(HTTPError):
    """Viper rejected the token; it was renewed, but the request was not sent again."""


class ViperAuth(AuthBase):
    def __init__(
        self,
        auth: tuple[str, str],
        login: Callable[..., AuthResponse],
        refresh: Callable[..., AuthResponse],
    ):
        super().__init__()
        self._lock = RLock()
        self._recursion_guard = False
        self.auth_info = AuthInfo(*auth)
        self.login = login
        self.refresh = refresh

    def auth_wrap(self, f):
        if hasattr(f, "_auth_wrapped"):
            return f

        @wraps(f)
        def wrapper(*args, replay_on_token_failure: bool = True, **kwargs):
            active_auth = kwargs.setdefault("auth", self)

            # Explicit auth=None is used for login and static Bearer tokens.
            if active_auth is not self:
                return f(*args, **kwargs)

            try:
                return f(*args, **kwargs)
            except HTTPError as exc:
                response = exc.response
                if response is None or response.status_code != 401:
                    raise

                try:
                    error = ErrorItem.from_json(response.text)
                    error_code = error.error.code
                except Exception:
                    raise exc

                if error_code != "TOKEN_FAILURE":
                    raise

                with self._lock:
                    # Let update_token handle a rejected refresh itself.
                    if self._recursion_guard:
                        raise

                    sent_headers = getattr(response.request, "headers", {})
                    rejected_token = sent_headers.get("Authorization")
                    current_token = f"Bearer {self.auth_info.access_token}"

                    # Another thread may already have replaced this token.
                    if rejected_token is None or rejected_token == current_token:
                        self.update_token(force=True)

                if not replay_on_token_failure:
                    # Requests that start work, such as a batch, must not run twice.
                    raise ViperTokenRenewed(response=response) from exc
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
                try:
                    # Viper requires a valid access token on its refresh route.
                    if (
                        not self.auth_info.access_valid()
                        or not self.auth_info.refresh_valid()
                    ):
                        raise ValueError("Login required.")

                    requested_at = time.monotonic()
                    response = self.refresh(refresh_token=self.auth_info.refresh_token)
                    self.auth_info.update_with_response(response, requested_at)
                    return
                except (ValueError, HTTPError) as exc:
                    if isinstance(exc, HTTPError):
                        if exc.response is None or exc.response.status_code not in (
                            400,
                            401,
                            403,
                            422,
                        ):
                            raise

                requested_at = time.monotonic()
                response = self.login(
                    username=self.auth_info.username,
                    password=self.auth_info.password,
                )
                self.auth_info.update_with_response(response, requested_at)
            finally:
                self._recursion_guard = False

    def __call__(self, request):
        with self._lock:
            self.update_token()
            request.headers["Authorization"] = f"Bearer {self.auth_info.access_token}"
        return request
