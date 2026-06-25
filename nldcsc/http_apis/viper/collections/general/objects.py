from dataclasses import dataclass
from typing import Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class AppDetailsResponse(DataClassJsonMixin):
    application_name: str
    application_build_version: str


@dataclass
class EndpointMaintenanceWindow(DataClassJsonMixin):
    start: int
    end: int
    reason: str


@dataclass
class EndpointRateLimitPolicy(DataClassJsonMixin):
    algorithm: str
    strategy: str
    limit: str
    method: str
    path: str


@dataclass
class EndpointsEntry(DataClassJsonMixin):
    path: str
    status: str
    reason: str
    method: str
    url: str
    rollout_percentage: int
    rate_limit_policy: Optional[EndpointRateLimitPolicy] = None
    service: Optional[str] = None
    sunset_date: Optional[str] = None
    maintenance_window: Optional[EndpointMaintenanceWindow] = None
    successor_path: Optional[str] = None


@dataclass
class EndpointDetailsResponse(DataClassJsonMixin):
    endpoints: list[EndpointsEntry]
