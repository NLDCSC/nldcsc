from dataclasses import dataclass

from dataclasses_json import DataClassJsonMixin


@dataclass
class AssetResponse(DataClassJsonMixin):
    page_number: int
    page_size: int
    total_pages: int
    total_resources: int
    resources: list[dict]


@dataclass
class Vulnerabilities(DataClassJsonMixin):
    vulnerabilities: list[dict]


@dataclass
class Solutions(DataClassJsonMixin):
    solutions: list[dict]
