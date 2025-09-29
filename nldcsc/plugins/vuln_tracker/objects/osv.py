from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import config as json_config
from dataclasses_json import dataclass_json

from nldcsc.generic.utils import exclude_optional_dict
from nldcsc.plugins.vuln_tracker.objects.data_class_validations import Validations


@dataclass_json
@dataclass
class Severity(Validations):
    type: str
    score: str


@dataclass_json
@dataclass
class Package(Validations):
    ecosystem: str
    name: str

    purl: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class Event(Validations):
    introduced: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    fixed: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    last_affected: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    limit: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class Range(Validations):
    type: str
    events: list[Event]

    repo: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    database_specific: Optional[dict] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if isinstance(self.events, list):
            self.events = [Event(**dict(x)) for x in self.events]


@dataclass_json
@dataclass
class Affected(Validations):
    package: Optional[Package] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    severity: Optional[Severity] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    ranges: Optional[list[Range]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    versions: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    ecosystem_specific: Optional[dict] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    database_specific: Optional[dict] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if isinstance(self.package, dict):
            self.package = Package(**self.package)

        if isinstance(self.severity, dict):
            self.severity = Severity(**self.severity)

        if hasattr(self, "ranges"):
            if isinstance(self.ranges, list):
                self.ranges = [Range(**dict(x)) for x in self.ranges]


@dataclass_json
@dataclass
class Reference(Validations):
    type: str
    url: str


@dataclass_json
@dataclass
class Credit(Validations):
    name: str

    type: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    contact: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class OSV(Validations):
    id: str
    modified: str

    schema_version: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    published: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    withdrawn: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    aliases: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    related: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    upstream: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    summary: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    details: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    severity: Optional[list[Severity]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    affected: Optional[list[Affected]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    references: Optional[list[Reference]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    credits: Optional[list[Credit]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    database_specific: Optional[dict] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if hasattr(self, "severity"):
            if isinstance(self.severity, list):
                self.severity = [Severity(**dict(x)) for x in self.severity]

        if hasattr(self, "affected"):
            if isinstance(self.affected, list):
                self.affected = [Affected(**dict(x)) for x in self.affected]

        if hasattr(self, "references"):
            if isinstance(self.references, list):
                self.references = [Reference(**dict(x)) for x in self.references]

        if hasattr(self, "credits"):
            if isinstance(self.credits, list):
                self.credits = [Credit(**dict(x)) for x in self.credits]

    @property
    def cve_id(self) -> str:
        return f"{self.id}"

    @property
    def publisher(self) -> str:
        return self.id.split("-")[0]

    def __repr__(self) -> str:
        return f"OSV({self.publisher}[{self.id}])"
