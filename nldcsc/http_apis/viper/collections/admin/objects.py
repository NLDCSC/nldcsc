from dataclasses import dataclass, field

from dataclasses_json import DataClassJsonMixin, LetterCase, config


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
