from dataclasses import dataclass
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
class LogoutResponse(DataClassJsonMixin):
    msg: str
