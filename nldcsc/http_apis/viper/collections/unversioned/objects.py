from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin


@dataclass
class WelcomeResponse(DataClassJsonMixin):
    message: str
    documentation: str


@dataclass
class ChangelogMemberChanges(DataClassJsonMixin):
    name: str
    status: str
    old_value: str
    new_value: str


@dataclass
class ChangelogChanges(DataClassJsonMixin):
    description: str
    side_effects: bool
    instructions: list[dict]


@dataclass
class ChangelogVersion(DataClassJsonMixin):
    value: str
    changes: list[ChangelogChanges]


@dataclass
class ChangelogResponse(DataClassJsonMixin):
    versions: list[ChangelogVersion]
