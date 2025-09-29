import json
from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import config as json_config
from dataclasses_json import dataclass_json

from nldcsc.generic.utils import exclude_optional_dict
from nldcsc.plugins.vuln_tracker.objects.common import CVSS40, CVSS31, CVSS30, CVSS2
from nldcsc.plugins.vuln_tracker.objects.data_class_validations import Validations


@dataclass_json
@dataclass
class Reference(Validations):
    url: str

    source: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    tags: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class LangString(Validations):
    lang: str
    value: str


@dataclass_json
@dataclass
class Cvss40(Validations):
    source: str
    type: str
    cvssData: CVSS40

    def __post_init__(self):
        if isinstance(self.cvssData, dict):
            self.cvssData = CVSS40(**self.cvssData)


@dataclass_json
@dataclass
class Cvss31(Validations):
    source: str
    type: str
    cvssData: CVSS31

    exploitabilityScore: Optional[int] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    impactScore: Optional[int] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if isinstance(self.cvssData, dict):
            self.cvssData = CVSS31(**self.cvssData)


@dataclass_json
@dataclass
class Cvss30(Validations):
    source: str
    type: str
    cvssData: CVSS30

    exploitabilityScore: Optional[int] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    impactScore: Optional[int] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if isinstance(self.cvssData, dict):
            self.cvssData = CVSS30(**self.cvssData)


@dataclass_json
@dataclass
class Cvss2(Validations):
    source: str
    type: str
    cvssData: CVSS2

    baseSeverity: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    exploitabilityScore: Optional[int] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    impactScore: Optional[int] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    acInsufInfo: Optional[bool] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    obtainAllPrivilege: Optional[bool] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    obtainUserPrivilege: Optional[bool] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    obtainOtherPrivilege: Optional[bool] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    userInteractionRequired: Optional[bool] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if isinstance(self.cvssData, dict):
            self.cvssData = CVSS2(**self.cvssData)


@dataclass_json
@dataclass
class Metric(Validations):
    cvssMetricV40: Optional[list[Cvss40]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    cvssMetricV31: Optional[list[Cvss31]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    cvssMetricV30: Optional[list[Cvss30]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    cvssMetricV2: Optional[list[Cvss2]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if hasattr(self, "cvssMetricV40"):
            if isinstance(self.cvssMetricV40, list):
                self.cvssMetricV40 = [Cvss40(**dict(x)) for x in self.cvssMetricV40]

        if hasattr(self, "cvssMetricV31"):
            if isinstance(self.cvssMetricV31, list):
                self.cvssMetricV31 = [Cvss31(**dict(x)) for x in self.cvssMetricV31]

        if hasattr(self, "cvssMetricV30"):
            if isinstance(self.cvssMetricV30, list):
                self.cvssMetricV30 = [Cvss30(**dict(x)) for x in self.cvssMetricV30]

        if hasattr(self, "cvssMetricV2"):
            if isinstance(self.cvssMetricV2, list):
                self.cvssMetricV2 = [Cvss2(**dict(x)) for x in self.cvssMetricV2]


@dataclass_json
@dataclass
class Weakness(Validations):
    source: str
    type: str
    description: list[LangString]

    def __post_init__(self):
        if isinstance(self.description, list):
            self.description = [LangString(**dict(x)) for x in self.description]


@dataclass_json
@dataclass
class CpeMatch(Validations):
    vulnerable: bool
    criteria: str
    matchCriteriaId: str

    versionStartExcluding: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    versionStartIncluding: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    versionEndExcluding: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    versionEndIncluding: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class Node(Validations):
    operator: str
    cpeMatch: list[CpeMatch]

    negate: Optional[bool] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if isinstance(self.cpeMatch, list):
            self.cpeMatch = [CpeMatch(**dict(x)) for x in self.cpeMatch]


@dataclass_json
@dataclass
class NistConfig(Validations):
    nodes: list[Node]

    operator: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    negate: Optional[bool] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if isinstance(self.nodes, list):
            self.nodes = [Node(**dict(x)) for x in self.nodes]


@dataclass_json
@dataclass
class VendorComment(Validations):
    organization: str
    comment: str
    lastModified: str


@dataclass_json
@dataclass
class Nist(Validations):
    id: str
    published: str
    lastModified: str
    references: list[Reference]
    descriptions: list[LangString]

    sourceIdentifier: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    vulnStatus: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    evaluatorComment: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    evaluatorSolution: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    evaluatorImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    cisaExploitAdd: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    cisaActionDue: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    cisaRequiredAction: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    cisaVulnerabilityName: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    cveTags: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    metrics: Optional[Metric] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    weaknesses: Optional[list[Weakness]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    configurations: Optional[list[NistConfig]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    vendorComments: Optional[list[VendorComment]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def to_rss_format(self):

        return {
            "id": self.id,
            "published": self.published,
            "lastModified": self.lastModified,
            "descriptions": f"{[x.value for x in self.descriptions if x.lang == 'en']}",
            "references": f"{[x.url for x in self.references]}",
        }

    def __post_init__(self):
        if isinstance(self.references, list):
            self.references = [Reference(**dict(x)) for x in self.references]

        if isinstance(self.descriptions, list):
            self.descriptions = [LangString(**dict(x)) for x in self.descriptions]

        if hasattr(self, "metrics"):
            if isinstance(self.metrics, dict):
                self.metrics = Metric(**self.metrics)

        if hasattr(self, "weaknesses"):
            if isinstance(self.weaknesses, list):
                self.weaknesses = [Weakness(**dict(x)) for x in self.weaknesses]

        if hasattr(self, "configurations"):
            if isinstance(self.configurations, list):
                self.configurations = [
                    NistConfig(**dict(x)) for x in self.configurations
                ]

        if hasattr(self, "vendorComments"):
            if isinstance(self.vendorComments, list):
                self.vendorComments = [
                    VendorComment(**dict(x)) for x in self.vendorComments
                ]

    @property
    def cve_id(self) -> str:
        return f"{self.id}"

    @property
    def publisher(self) -> str:
        return f"{self.sourceIdentifier}"

    def __eq__(self, other: "Nist") -> bool:
        return self.to_dict() == other.to_dict()

    def __lt__(self, other: "Nist") -> bool:
        return self.cve_id < other.cve_id

    def __repr__(self) -> str:
        return f"Nist({self.sourceIdentifier}[{self.id}])"


@dataclass_json
@dataclass
class NistCveHistoryDetail(Validations):
    type: str

    action: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    oldValue: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    newValue: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class NistCveHistory(Validations):
    cveId: str
    eventName: str
    cveChangeId: str
    sourceIdentifier: str

    created: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    details: Optional[list[NistCveHistoryDetail]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if hasattr(self, "details"):
            if isinstance(self.details, list):
                self.details = [NistCveHistoryDetail(**dict(x)) for x in self.details]

    def __repr__(self) -> str:
        return f"NistCveHistory({self.sourceIdentifier}[{self.cveId}])"


@dataclass_json
@dataclass
class Title(Validations):
    title: str
    lang: str


@dataclass_json
@dataclass
class CpeReference(Validations):
    ref: str

    type: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class DepCpe(Validations):
    cpeName: str
    cpeNameId: str


@dataclass_json
@dataclass
class NistCpe(Validations):
    deprecated: bool
    cpeName: str
    cpeNameId: str
    created: str
    lastModified: str

    titles: Optional[list[Title]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    refs: Optional[list[CpeReference]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    deprecatedBy: Optional[list[DepCpe]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    deprecates: Optional[list[DepCpe]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if isinstance(self.deprecated, str):
            self.deprecated = json.loads(self.deprecated)

        if hasattr(self, "titles"):
            if isinstance(self.titles, list):
                self.titles = [
                    Title(**dict(x)) for x in self.titles if dict(x)["lang"] == "en"
                ]
            if isinstance(self.titles, str):
                self.titles = [Title(**dict(x)) for x in json.loads(self.titles)]

        if hasattr(self, "refs"):
            if isinstance(self.refs, list):
                self.refs = [CpeReference(**dict(x)) for x in self.refs]
            if isinstance(self.refs, str):
                self.refs = [CpeReference(**dict(x)) for x in json.loads(self.refs)]

        if hasattr(self, "deprecatedBy"):
            if isinstance(self.deprecatedBy, list):
                self.deprecatedBy = [DepCpe(**dict(x)) for x in self.deprecatedBy]
            if isinstance(self.deprecatedBy, str):
                self.deprecatedBy = [
                    DepCpe(**dict(x)) for x in json.loads(self.deprecatedBy)
                ]

        if hasattr(self, "deprecates"):
            if isinstance(self.deprecates, list):
                self.deprecates = [DepCpe(**dict(x)) for x in self.deprecates]
            if isinstance(self.deprecates, str):
                self.deprecates = [
                    DepCpe(**dict(x)) for x in json.loads(self.deprecates)
                ]

    def to_redis(self):
        data = self.to_dict()

        data["deprecated"] = json.dumps(data["deprecated"])

        if "titles" in data:
            data["titles"] = json.dumps(data["titles"])
        if "refs" in data:
            data["refs"] = json.dumps(data["refs"])
        if "deprecatedBy" in data:
            data["deprecatedBy"] = json.dumps(data["deprecatedBy"])
        if "deprecates" in data:
            data["deprecates"] = json.dumps(data["deprecates"])

        return data

    def __repr__(self) -> str:
        if self.deprecated:
            return f"NistCpe({self.cpeName}[{self.cpeNameId}]) **DEPRECATED**"
        else:
            return f"NistCpe({self.cpeName}[{self.cpeNameId}])"


@dataclass_json
@dataclass
class CpeName(Validations):
    cpeName: str
    cpeNameId: str


@dataclass_json
@dataclass
class NistCpeMatch(Validations):
    criteria: str
    matchCriteriaId: str
    created: str
    lastModified: str
    status: str

    versionStartExcluding: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    versionStartIncluding: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    versionEndExcluding: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    versionEndIncluding: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    cpeLastModified: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    matches: Optional[list[CpeName]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if hasattr(self, "matches"):
            if isinstance(self.matches, list):
                self.matches = [CpeName(**dict(x)) for x in self.matches]
            if isinstance(self.matches, str):
                self.matches = [CpeName(**dict(x)) for x in json.loads(self.matches)]

    def __repr__(self) -> str:
        return f"NistCpeMatch({self.criteria}[{self.matchCriteriaId}])"

    def to_redis(self):
        data = self.to_dict()

        if "matches" in data:
            data["matches"] = json.dumps(data["matches"])

        return data
