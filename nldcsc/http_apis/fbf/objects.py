from dataclasses import dataclass, field
from typing import Any, Optional
from dataclasses_json import DataClassJsonMixin, config


@dataclass
class FBFErrors(DataClassJsonMixin):
    errors: list[str] | str


@dataclass
class FBFInfo(DataClassJsonMixin):
    application_name: str = field(metadata=config(field_name="ApplicationName"))
    application_version: str = field(metadata=config(field_name="ApplicationVersion"))


@dataclass
class NCSCFeedInfo(DataClassJsonMixin):
    feeds: list[str]


@dataclass
class NCSCFeedUpdate(DataClassJsonMixin):
    count: int


@dataclass
class NCSCFeedUpdateSquence(DataClassJsonMixin):
    timestamp: int
    updates: list[NCSCFeedUpdate]


@dataclass
class NCSCFeedUpdateSequenceList(DataClassJsonMixin):
    entries: list[NCSCFeedUpdateSquence]


@dataclass
class NCSCFeedIndex(DataClassJsonMixin):
    name: str
    request_id: str
    index: str
    total_count: int
    start_time: Optional[int] = None
    stop_time: Optional[int] = None


@dataclass
class NCSCFeedItems(DataClassJsonMixin):
    entries: list[Any]
    entries_count: int
    total_count: int
    request_id: str
    limit: int
    offset: int
    last: bool


@dataclass
class NCSCFeedUpdateTS(DataClassJsonMixin):
    name: str
    timestamp: int
