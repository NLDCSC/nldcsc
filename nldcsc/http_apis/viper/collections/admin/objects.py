from dataclasses import dataclass, field
from enum import IntEnum, auto

from dataclasses_json import DataClassJsonMixin, LetterCase, config

from nldcsc.http_apis.viper.collections.bases import PaginatedResponse


class UserAction(IntEnum):
    LOGIN = 0
    LOGOUT = auto()
    REQUEST = auto()
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()
    REFRESH_TOKEN = auto()


@dataclass
class RedisInfo:
    connected_clients: int
    redis_mode: str
    redis_version: str
    total_system_memory_human: str
    used_memory_human: str
    uptime_in_days: int
    uptime_in_seconds: int


@dataclass
class TaskState(DataClassJsonMixin):
    task_received: int = field(metadata=config(letter_case=LetterCase.KEBAB))
    task_succeeded: int = field(metadata=config(letter_case=LetterCase.KEBAB))


@dataclass
class StatusResponse(DataClassJsonMixin):
    redis_info: RedisInfo
    celery_info: dict[str, dict[str, TaskState]]


@dataclass
class AuditItem(DataClassJsonMixin):
    id: str
    timestamp: int
    username: str
    user_action: UserAction
    origin: str
    affected_resources: dict
    description: str
    tags: list[str]
    request_id: str


@dataclass
class AuditLogResponse(PaginatedResponse[AuditItem]): ...
