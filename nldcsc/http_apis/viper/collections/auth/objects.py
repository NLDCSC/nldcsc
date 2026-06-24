from dataclasses import dataclass
import time
from dataclasses_json import DataClassJsonMixin


@dataclass
class AuthResponse(DataClassJsonMixin):
    access_token: str
    expires_in: int
    refresh_token: str
    refresh_expires_in: int
    token_type: str
    id_token: str
    scope: str
    session_state: str


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
