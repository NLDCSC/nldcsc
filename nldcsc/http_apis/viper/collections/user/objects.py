from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Optional

from dataclasses_json import DataClassJsonMixin

from nldcsc.http_apis.viper.collections.bases import PaginatedResponse


class AsyncSearchState(StrEnum):
    ALL = auto()
    CREATED = auto()
    STARTED = auto()
    COMPLETED = auto()


@dataclass
class MeResponse(DataClassJsonMixin):
    user_id: str
    preferred_username: str
    email: str


@dataclass
class AsyncSearchItem(DataClassJsonMixin):
    id: str
    user_id: str
    created: int
    search_query: dict
    task_id: str
    completed: Optional[int] = None
    started: Optional[int] = None
    error: Optional[str] = None
    result: Optional[int] = None


@dataclass
class AsyncSearchesResponse(PaginatedResponse):
    items: list[AsyncSearchItem]
