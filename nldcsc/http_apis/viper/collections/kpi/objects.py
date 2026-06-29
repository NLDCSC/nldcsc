from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Optional

from dataclasses_json import DataClassJsonMixin

from nldcsc.http_apis.viper.collections.bases import PaginatedResponse


class KPIType(StrEnum):
    STR = auto()
    INT = auto()
    PERCENTAGE = auto()


@dataclass
class KPIItem(DataClassJsonMixin):
    name: str
    value: str
    kpi_type: str
    timestamp: int
    description: str
    unit: str
    worst_value: Optional[int] | None = None
    best_value: Optional[int] | None = None
    target_threshold: Optional[int] | None = None
    team: Optional[str] | None = None
    frequency: Optional[str] | None = None


@dataclass
class KPIResponse(PaginatedResponse):
    items: list[KPIItem]
