from dataclasses import dataclass, field
from inspect import signature
from typing import Optional

from dataclasses_json import config as json_config
from dataclasses_json import dataclass_json

from nldcsc.generic.utils import exclude_optional_dict
from nldcsc.plugins.vuln_tracker.objects.common import CVSS40, CVSS30, CVSS31, CVSS2
from nldcsc.plugins.vuln_tracker.objects.data_class_validations import Validations
from nldcsc.plugins.vuln_tracker.objects.osv import Affected


@dataclass_json
@dataclass
class Metadata(Validations):
    cveId: str
    assignerOrgId: str
    state: str

    assignerShortName: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    requesterUserId: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    dateUpdated: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    serial: Optional[int] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    dateReserved: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    datePublished: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    dateRejected: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class CNAInfo(Validations):
    orgId: str

    shortName: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    dateUpdated: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class Media(Validations):
    type: str
    value: str

    base64: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class Description(Validations):
    lang: str
    value: str

    supportingMedia: Optional[Media] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if hasattr(self, "supportingMedia"):
            if isinstance(self.supportingMedia, dict):
                self.supportingMedia = Media(**self.supportingMedia)


@dataclass_json
@dataclass
class ProgramRoutine(Validations):
    name: str


@dataclass_json
@dataclass
class Change(Validations):
    at: str
    status: str


@dataclass_json
@dataclass
class Version(Validations):
    version: str
    status: str

    versionType: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    lessThan: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    lessThanOrEqual: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    changes: Optional[list[Change]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if isinstance(self.changes, list):
            self.changes = [Change(**dict(x)) for x in self.changes]


@dataclass_json
@dataclass
class Affected(Validations):
    vendor: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    product: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    collectionURL: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    packageName: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    cpes: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modules: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    programFiles: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    programRoutines: Optional[list[ProgramRoutine]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    platforms: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    repo: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    defaultStatus: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    versions: Optional[list[Version]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if isinstance(self.programRoutines, list):
            self.programRoutines = [
                ProgramRoutine(**dict(x)) for x in self.programRoutines
            ]

        if isinstance(self.versions, list):
            self.versions = [Version(**dict(x)) for x in self.versions]


@dataclass_json
@dataclass
class Reference(Validations):
    url: str

    name: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    tags: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class ProblemTypeDescription(Validations):
    lang: str
    description: str

    cweId: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    type: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    references: Optional[Reference] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if hasattr(self, "references"):
            if isinstance(self.references, dict):
                self.references = Reference(**self.references)


@dataclass_json
@dataclass
class ProblemType(Validations):
    descriptions: list[ProblemTypeDescription]

    def __post_init__(self):
        if isinstance(self.descriptions, list):
            self.descriptions = [
                ProblemTypeDescription(**dict(x)) for x in self.descriptions
            ]


@dataclass_json
@dataclass
class Impact(Validations):
    descriptions: list[Description]

    capecId: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if isinstance(self.descriptions, list):
            self.descriptions = [Description(**dict(x)) for x in self.descriptions]


@dataclass_json
@dataclass
class Scenario(Validations):
    lang: str
    value: str


@dataclass_json
@dataclass
class Other(Validations):
    type: str
    content: dict


@dataclass_json
@dataclass
class Metric(Validations):
    format: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    scenarios: Optional[list[Scenario]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    cvssV4_0: Optional[CVSS40] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    cvssV3_1: Optional[CVSS31] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    cvssV3_0: Optional[CVSS30] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    cvssV2_0: Optional[CVSS2] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    other: Optional[Other] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if hasattr(self, "scenarios"):
            if isinstance(self.scenarios, list):
                self.scenarios = [Scenario(**dict(x)) for x in self.scenarios]

        if hasattr(self, "cvssV4_0"):
            if isinstance(self.cvssV4_0, dict):
                self.cvssV4_0 = CVSS40(**self.cvssV4_0)

        if hasattr(self, "cvssV3_1"):
            if isinstance(self.cvssV3_1, dict):
                self.cvssV3_1 = CVSS31(**self.cvssV3_1)

        if hasattr(self, "cvssV3_0"):
            if isinstance(self.cvssV3_0, dict):
                self.cvssV3_0 = CVSS30(**self.cvssV3_0)

        if hasattr(self, "cvssV2_0"):
            if isinstance(self.cvssV2_0, dict):
                self.cvssV2_0 = CVSS2(**self.cvssV2_0)

        if hasattr(self, "other"):
            if isinstance(self.other, dict):
                self.other = Other(**self.other)


@dataclass_json
@dataclass
class Timeline(Validations):
    time: str
    lang: str
    value: str


@dataclass_json
@dataclass
class Credit(Validations):
    lang: str
    value: str

    user: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    type: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class TaxonomyRelation(Validations):
    taxonomyId: str
    relationshipId: str
    relationshipValue: str


@dataclass_json
@dataclass
class TaxonomyMapping(Validations):
    taxonomyName: str
    taxonomyRelations: list[TaxonomyRelation]

    taxonomyVersion: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if isinstance(self.taxonomyRelations, list):
            self.taxonomyRelations = [
                TaxonomyRelation(**dict(x)) for x in self.taxonomyRelations
            ]


@dataclass_json
@dataclass
class CNARejected(Validations):
    providerMetadata: CNAInfo
    rejectedReasons: list[Description] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    replacedBy: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    @classmethod
    def from_kwargs(cls, **kwargs):
        # fetch the constructor's signature
        cls_fields = {field for field in signature(cls).parameters}

        # split the kwargs into native ones and new ones
        native_args, new_args = {}, {}
        for name, val in kwargs.items():
            if name in cls_fields:
                native_args[name] = val
            else:
                new_args[name] = val

        # use the native ones to create the class ...
        ret = cls(**native_args)

        # ... and add the new ones by hand
        for new_name, new_val in new_args.items():
            setattr(ret, new_name, new_val)
        return ret

    def to_rss_format(self):
        return {
            "rejectedReasons": f"{[x.value for x in self.rejectedReasons]}",
        }

    def __post_init__(self):
        if isinstance(self.providerMetadata, dict):
            self.providerMetadata = CNAInfo(**self.providerMetadata)

        if isinstance(self.rejectedReasons, list):
            self.rejectedReasons = [
                Description(**dict(x)) for x in self.rejectedReasons
            ]


@dataclass_json
@dataclass
class CNAPublished(Validations):
    providerMetadata: CNAInfo
    descriptions: list[Description]
    affected: list[Affected]
    references: list[Reference]

    dateAssigned: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    datePublic: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    title: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    problemTypes: Optional[list[ProblemType]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    impacts: Optional[list[Impact]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    metrics: Optional[list[Metric]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    configurations: Optional[list[Description]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    workarounds: Optional[list[Description]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    solutions: Optional[list[Description]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    exploits: Optional[list[Description]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    timeline: Optional[list[Timeline]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    credits: Optional[list[Credit]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    source: Optional[dict] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    tags: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    taxonomyMappings: Optional[list[TaxonomyMapping]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    @classmethod
    def from_kwargs(cls, **kwargs):
        # fetch the constructor's signature
        cls_fields = {field for field in signature(cls).parameters}

        # split the kwargs into native ones and new ones
        native_args, new_args = {}, {}
        for name, val in kwargs.items():
            if name in cls_fields:
                native_args[name] = val
            else:
                new_args[name] = val

        # use the native ones to create the class ...
        ret = cls(**native_args)

        # ... and add the new ones by hand
        for new_name, new_val in new_args.items():
            setattr(ret, new_name, new_val)
        return ret

    def to_rss_format(self):

        if len(self.affected) == 1:
            return {
                "product": self.affected[0].product,
                "vendor": self.affected[0].vendor,
                "versions": f"{[{'status': x.status, 'version': x.version} for x in self.affected[0].versions]}",
                "descriptions": f"{[x.value for x in self.descriptions]}",
                "references": f"{[x.url for x in self.references]}",
            }
        else:
            return {
                "affected_products": f"Multiple products / vendors: {len(self.affected)}",
                "descriptions": f"{[x.value for x in self.descriptions]}",
                "references": f"{[x.url for x in self.references]}",
            }

    def __post_init__(self):
        if isinstance(self.providerMetadata, dict):
            self.providerMetadata = CNAInfo(**self.providerMetadata)

        if isinstance(self.descriptions, list):
            self.descriptions = [Description(**dict(x)) for x in self.descriptions]

        if isinstance(self.affected, list):
            self.affected = [Affected(**dict(x)) for x in self.affected]

        if isinstance(self.references, list):
            self.references = [Reference(**dict(x)) for x in self.references]

        if hasattr(self, "problemTypes"):
            if isinstance(self.problemTypes, list):
                self.problemTypes = [ProblemType(**dict(x)) for x in self.problemTypes]

        if hasattr(self, "impacts"):
            if isinstance(self.impacts, list):
                self.impacts = [Impact(**dict(x)) for x in self.impacts]

        if hasattr(self, "metrics"):
            if isinstance(self.metrics, list):
                self.metrics = [Metric(**dict(x)) for x in self.metrics]

        if hasattr(self, "configurations"):
            if isinstance(self.configurations, list):
                self.configurations = [
                    Description(**dict(x)) for x in self.configurations
                ]

        if hasattr(self, "workarounds"):
            if isinstance(self.workarounds, list):
                self.workarounds = [Description(**dict(x)) for x in self.workarounds]

        if hasattr(self, "solutions"):
            if isinstance(self.solutions, list):
                self.solutions = [Description(**dict(x)) for x in self.solutions]

        if hasattr(self, "exploits"):
            if isinstance(self.exploits, list):
                self.exploits = [Description(**dict(x)) for x in self.exploits]

        if hasattr(self, "timeline"):
            if isinstance(self.timeline, list):
                self.timeline = [Timeline(**dict(x)) for x in self.timeline]

        if hasattr(self, "credits"):
            if isinstance(self.credits, list):
                self.credits = [Credit(**dict(x)) for x in self.credits]

        if hasattr(self, "taxonomyMappings"):
            if isinstance(self.taxonomyMappings, list):
                self.taxonomyMappings = [
                    TaxonomyMapping(**dict(x)) for x in self.taxonomyMappings
                ]


@dataclass_json
@dataclass
class ADP(Validations):
    providerMetadata: CNAInfo

    descriptions: Optional[list[Description]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    affected: Optional[list[Affected]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    references: Optional[list[Reference]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    dateAssigned: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    datePublic: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    title: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    problemTypes: Optional[list[ProblemType]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    impacts: Optional[list[Impact]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    metrics: Optional[list[Metric]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    configurations: Optional[list[Description]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    workarounds: Optional[list[Description]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    solutions: Optional[list[Description]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    exploits: Optional[list[Description]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    timeline: Optional[list[Timeline]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    credits: Optional[list[Credit]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    source: Optional[dict] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    tags: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    taxonomyMappings: Optional[list[TaxonomyMapping]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    # this one might need some dynamic handling, all object with starting x (Pattern property)
    x_generator: Optional[dict] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if isinstance(self.providerMetadata, dict):
            self.providerMetadata = CNAInfo(**self.providerMetadata)

        if hasattr(self, "descriptions"):
            if isinstance(self.descriptions, list):
                self.descriptions = [Description(**dict(x)) for x in self.descriptions]

        if hasattr(self, "affected"):
            if isinstance(self.affected, list):
                self.affected = [Affected(**dict(x)) for x in self.affected]

        if hasattr(self, "references"):
            if isinstance(self.references, list):
                self.references = [Reference(**dict(x)) for x in self.references]

        if hasattr(self, "problemTypes"):
            if isinstance(self.problemTypes, list):
                self.problemTypes = [ProblemType(**dict(x)) for x in self.problemTypes]

        if hasattr(self, "impacts"):
            if isinstance(self.impacts, list):
                self.impacts = [Impact(**dict(x)) for x in self.impacts]

        if hasattr(self, "metrics"):
            if isinstance(self.metrics, list):
                self.metrics = [Metric(**dict(x)) for x in self.metrics]

        if hasattr(self, "configurations"):
            if isinstance(self.configurations, list):
                self.configurations = [
                    Description(**dict(x)) for x in self.configurations
                ]

        if hasattr(self, "workarounds"):
            if isinstance(self.workarounds, list):
                self.workarounds = [Description(**dict(x)) for x in self.workarounds]

        if hasattr(self, "solutions"):
            if isinstance(self.solutions, list):
                self.solutions = [Description(**dict(x)) for x in self.solutions]

        if hasattr(self, "exploits"):
            if isinstance(self.exploits, list):
                self.exploits = [Description(**dict(x)) for x in self.exploits]

        if hasattr(self, "timeline"):
            if isinstance(self.timeline, list):
                self.timeline = [Timeline(**dict(x)) for x in self.timeline]

        if hasattr(self, "credits"):
            if isinstance(self.credits, list):
                self.credits = [Credit(**dict(x)) for x in self.credits]

        if hasattr(self, "taxonomyMappings"):
            if isinstance(self.taxonomyMappings, list):
                self.taxonomyMappings = [
                    TaxonomyMapping(**dict(x)) for x in self.taxonomyMappings
                ]


@dataclass_json
@dataclass
class Containers(Validations):
    cna: CNAPublished | CNARejected
    cna_type: str = "published"

    adp: Optional[ADP] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if isinstance(self.cna, dict):
            if self.cna_type == "published":
                self.cna = CNAPublished.from_kwargs(**self.cna)
            else:
                self.cna = CNARejected.from_kwargs(**self.cna)

        if hasattr(self, "adp"):
            if isinstance(self.adp, dict):
                self.adp = ADP(**self.adp)

        delattr(self, "cna_type")


@dataclass_json
@dataclass
class CveRecord(Validations):
    dataType: str
    dataVersion: str
    cveMetadata: Metadata
    containers: Containers

    @property
    def cve_id(self) -> str:
        return f"{self.cveMetadata.cveId}"

    @property
    def state(self) -> str:
        return f"{self.cveMetadata.state}"

    def to_rss_format(self) -> dict:

        ret_dict = {
            "cve_id": self.cve_id,
            "state": self.state,
            "shortName": self.containers.cna.providerMetadata.shortName,
        }

        ret_dict.update(self.containers.cna.to_rss_format())

        return ret_dict

    def __repr__(self) -> str:
        return f"CVE_RECORD({self.state}[{self.cve_id}])"

    def __post_init__(self):
        if isinstance(self.cveMetadata, dict):
            self.cveMetadata = Metadata(**self.cveMetadata)

        if isinstance(self.containers, dict):
            self.containers = Containers(
                **self.containers, cna_type=self.cveMetadata.state.lower()
            )
