from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin


@dataclass
class MeResponse(DataClassJsonMixin):
    user_id: str
    preferred_username: str
    email: str
