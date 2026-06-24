from dataclasses import dataclass
from typing import Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class ErrorDescription(DataClassJsonMixin):
    code: str
    message: str
    request_id: str
    status_code: int
    details: Optional[str] | None = None


@dataclass
class ErrorItem(DataClassJsonMixin):
    error: ErrorDescription


@dataclass
class DetailResponse(DataClassJsonMixin):
    detail: str
