from dataclasses import dataclass
from enum import auto

from dataclasses_json import DataClassJsonMixin

from nldcsc.http_apis.viper.collections.bases import PaginatedResponse
from nldcsc.http_apis.viper.objects import UpperCaseStrEnum


class OTAP(UpperCaseStrEnum):
    O = auto()
    T = auto()
    A = auto()
    P = auto()


@dataclass
class OracleDBItem(DataClassJsonMixin):
    db_id: int
    hostname: str
    maintainer: str
    db_name: str
    otap: OTAP


@dataclass
class OracleDBResponse(DataClassJsonMixin):
    entries: list[OracleDBItem]


@dataclass
class OracleDBCreateResponse(OracleDBResponse): ...


@dataclass
class OracleDBModifyResponse(OracleDBResponse): ...


@dataclass
class OracleDBSearchResponse(PaginatedResponse[OracleDBItem]): ...
