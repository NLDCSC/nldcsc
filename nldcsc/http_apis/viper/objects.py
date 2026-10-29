from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Any, Optional

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
class AsyncSearchesResponse(PaginatedResponse[AsyncSearchItem]): ...


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


@dataclass
class SearchExclusion(DataClassJsonMixin):
    """One AND NOT term: leave out records where field matches value."""

    field: str
    value: str


@dataclass
class BatchSearchQuery(DataClassJsonMixin):
    """One search in a batch: a source (connector.id) and what to look for."""

    connector_id: str
    field: str
    value: str
    page: int = 0
    size: int = 10
    exclusions: Optional[list[SearchExclusion]] = None


@dataclass
class BatchSearchItem(DataClassJsonMixin):
    """Vipers answer for a single search in a batch."""

    connector_id: str
    status_code: int
    search: Optional[AsyncSearchResponse] = None
    status_url: Optional[str] = None
    results_url: Optional[str] = None
    error: Any = None  # text, or {"code": ..., "message": ...}
    retry_after: Optional[str] = None  # only with 429

    @property
    def started(self) -> bool:
        return self.status_code == 201

    @property
    def error_code(self) -> str | None:
        return self.error.get("code") if isinstance(self.error, dict) else None


@dataclass
class BatchSearchResponse(DataClassJsonMixin):
    searches: list[BatchSearchItem]
