from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Optional

from dataclasses_json import DataClassJsonMixin

from nldcsc.http_apis.viper.collections.bases import PaginatedResponse


class UpperCaseStrEnum(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.upper()


class UpperCaseSpaceStrEnum(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.upper().replace("_", " ")


class ListOperator(UpperCaseSpaceStrEnum):
    IN = auto()
    NOT_IN = auto()


class ExtendedListOperator(UpperCaseSpaceStrEnum):
    IN = auto()
    NOT_IN = auto()
    IN_LIKE = auto()
    NOT_IN_LIKE = auto()


class IntOperator(UpperCaseStrEnum):
    GT = auto()
    LT = auto()
    EQ = auto()
    NE = auto()
    GE = auto()
    LE = auto()


class AsyncSearchState(StrEnum):
    ALL = auto()
    CREATED = auto()
    STARTED = auto()
    COMPLETED = auto()


@dataclass
class ErrorDescription(DataClassJsonMixin):
    code: str
    message: str
    request_id: str
    status_code: int
    details: Optional[str] = None


@dataclass
class ErrorItem(DataClassJsonMixin):
    error: ErrorDescription


@dataclass
class DetailResponse(DataClassJsonMixin):
    detail: str


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


@dataclass
class SuccessResponse:
    success: bool


class AsyncSearchStatus(UpperCaseStrEnum):
    CREATED = auto()
    STARTED = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass
class AsyncSearchResponse(DataClassJsonMixin):
    id: str
    error: str | None = None
    created: int | None = None
    completed: int | None = None
    status: AsyncSearchStatus | None = None
