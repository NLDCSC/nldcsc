from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import config as json_config
from dataclasses_json import dataclass_json

from nldcsc.generic.utils import exclude_optional_dict
from nldcsc.plugins.vuln_tracker.objects.common import CVSS2, CVSS30, CVSS31
from nldcsc.plugins.vuln_tracker.objects.data_class_validations import Validations


@dataclass_json
@dataclass
class Publisher(Validations):
    category: str
    name: str
    namespace: str

    contact_details: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    issuing_authority: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class Revision(Validations):
    date: str
    number: str
    summary: str

    legacy_version: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class Engine(Validations):
    name: str

    version: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class Generator(Validations):
    engine: Engine

    date: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if isinstance(self.engine, dict):
            self.engine = Engine(**self.engine)


@dataclass_json
@dataclass
class Tracking(Validations):
    current_release_date: str
    id: str
    initial_release_date: str
    revision_history: list[Revision]
    status: str
    version: str

    aliases: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    generator: Optional[Generator] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if isinstance(self.revision_history, list):
            self.revision_history = [Revision(**dict(x)) for x in self.revision_history]

        if hasattr(self, "generator"):
            if isinstance(self.generator, dict):
                self.generator = Generator(**self.generator)


@dataclass_json
@dataclass
class Acknowledgment(Validations):
    summary: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    organization: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    names: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    urls: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class AggregateSeverity(Validations):
    text: str

    namespace: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class TLP(Validations):
    label: str

    url: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class Distribution(Validations):
    text: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    tlp: Optional[TLP] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if hasattr(self, "tlp"):
            if isinstance(self.tlp, dict):
                self.tlp = TLP(**self.tlp)


@dataclass_json
@dataclass
class Note(Validations):
    category: str
    text: str

    title: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    audience: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class Reference(Validations):
    summary: str
    url: str

    category: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class Document(Validations):
    """Captures the meta-data about this document describing a particular set of security advisories."""

    category: str
    csaf_version: str
    publisher: Publisher
    title: str
    tracking: Tracking

    acknowledgments: Optional[list[Acknowledgment]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    aggregate_severity: Optional[AggregateSeverity] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    distribution: Optional[Distribution] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    lang: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    notes: Optional[list[Note]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    references: Optional[list[Reference]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    source_lang: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if isinstance(self.publisher, dict):
            self.publisher = Publisher(**self.publisher)

        if isinstance(self.tracking, dict):
            self.tracking = Tracking(**self.tracking)

        if hasattr(self, "acknowledgments"):
            if isinstance(self.acknowledgments, list):
                self.acknowledgments = [
                    Acknowledgment(**dict(x)) for x in self.acknowledgments
                ]

        if hasattr(self, "aggregate_severity"):
            if isinstance(self.aggregate_severity, dict):
                self.aggregate_severity = AggregateSeverity(**self.aggregate_severity)

        if hasattr(self, "distribution"):
            if isinstance(self.distribution, dict):
                self.distribution = Distribution(**self.distribution)

        if hasattr(self, "notes"):
            if isinstance(self.notes, list):
                self.notes = [Note(**dict(x)) for x in self.notes]

        if hasattr(self, "references"):
            if isinstance(self.references, list):
                self.references = [Reference(**dict(x)) for x in self.references]


@dataclass_json
@dataclass
class FileHash(Validations):
    algorithm: str
    value: str


@dataclass_json
@dataclass
class Hashes(Validations):
    filename: str
    file_hashes: list[FileHash]

    def __post_init__(self):
        if isinstance(self.file_hashes, list):
            self.file_hashes = [FileHash(**dict(x)) for x in self.file_hashes]


@dataclass_json
@dataclass
class GenericUri(Validations):
    namespace: str
    uri: str


@dataclass_json
@dataclass
class ProductIdHelper(Validations):
    cpe: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    hashes: Optional[list[Hashes]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    model_numbers: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    purl: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    sbom_urls: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    serial_numbers: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    skus: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    x_generic_uris: Optional[list[GenericUri]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if hasattr(self, "hashes"):
            if isinstance(self.hashes, list):
                self.hashes = [Hashes(**dict(x)) for x in self.hashes]

        if hasattr(self, "x_generic_uris"):
            if isinstance(self.x_generic_uris, list):
                self.x_generic_uris = [
                    GenericUri(**dict(x)) for x in self.x_generic_uris
                ]


@dataclass_json
@dataclass
class FullProductName(Validations):
    name: str
    product_id: str

    product_identification_helper: Optional[ProductIdHelper] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if hasattr(self, "product_identification_helper"):
            if isinstance(self.product_identification_helper, dict):
                self.product_identification_helper = ProductIdHelper(
                    **self.product_identification_helper
                )


@dataclass_json
@dataclass
class Branches(Validations):
    category: str
    name: str

    branches: Optional[list["Branches"]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    product: Optional[FullProductName] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if hasattr(self, "branches"):
            if isinstance(self.branches, list):
                self.branches = [Branches(**dict(x)) for x in self.branches]

        if hasattr(self, "product"):
            if isinstance(self.product, dict):
                self.product = FullProductName(**self.product)


@dataclass_json
@dataclass
class ProductGroup(Validations):
    group_id: str
    product_ids: list[str]

    summary: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class Relationship(Validations):
    category: str
    full_product_name: FullProductName
    product_reference: str
    relates_to_product_reference: str

    def __post_init__(self):
        if isinstance(self.full_product_name, dict):
            self.full_product_name = FullProductName(**self.full_product_name)


@dataclass_json
@dataclass
class ProductTree(Validations):
    branches: Optional[list[Branches]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    full_product_names: Optional[list[FullProductName]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    product_groups: Optional[list[ProductGroup]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    relationships: Optional[list[Relationship]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if hasattr(self, "branches"):
            if isinstance(self.branches, list):
                self.branches = [Branches(**dict(x)) for x in self.branches]

        if hasattr(self, "full_product_names"):
            if isinstance(self.full_product_names, list):
                self.full_product_names = [
                    FullProductName(**dict(x)) for x in self.full_product_names
                ]

        if hasattr(self, "product_groups"):
            if isinstance(self.product_groups, list):
                self.product_groups = [
                    ProductGroup(**dict(x)) for x in self.product_groups
                ]

        if hasattr(self, "relationships"):
            if isinstance(self.relationships, list):
                self.relationships = [
                    Relationship(**dict(x)) for x in self.relationships
                ]


@dataclass_json
@dataclass
class CWE(Validations):
    id: str
    name: str


@dataclass_json
@dataclass
class Flag(Validations):
    label: str

    date: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    group_ids: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    product_ids: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class ID(Validations):
    system_name: str
    text: str


@dataclass_json
@dataclass
class Involvement(Validations):
    party: str
    status: str

    date: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    summary: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class ProductStatus(Validations):
    first_affected: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    first_fixed: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    fixed: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    known_affected: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    known_not_affected: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    last_affected: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    recommended: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    under_investigation: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class RestartRequired(Validations):
    category: str

    details: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class Remediation(Validations):
    category: str
    details: str

    date: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    entitlements: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    group_ids: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    product_ids: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    restart_required: Optional[RestartRequired] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    url: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if hasattr(self, "restart_required"):
            if isinstance(self.restart_required, dict):
                self.restart_required = RestartRequired(**self.restart_required)


@dataclass_json
@dataclass
class Score(Validations):
    products: list[str]

    cvss_v2: Optional[CVSS2] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    cvss_v3: Optional[CVSS30 | CVSS31] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if hasattr(self, "cvss_v2"):
            if isinstance(self.cvss_v2, dict):
                self.cvss_v2 = CVSS2(**self.cvss_v2)

        if hasattr(self, "cvss_v3"):
            if isinstance(self.cvss_v3, dict):
                if self.cvss_v3["version"] == "3.0":
                    self.cvss_v3 = CVSS30(**self.cvss_v3)
                else:
                    self.cvss_v3 = CVSS31(**self.cvss_v3)


@dataclass_json
@dataclass
class Threat(Validations):
    category: str
    details: str

    date: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    group_ids: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    product_ids: Optional[list[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class Vulnerability(Validations):
    acknowledgments: Optional[list[Acknowledgment]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    cve: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    cwe: Optional[CWE] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    discovery_date: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    flags: Optional[list[Flag]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    ids: Optional[list[ID]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    involvements: Optional[list[Involvement]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    notes: Optional[list[Note]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    product_status: Optional[ProductStatus] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    references: Optional[list[Reference]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    release_date: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    remediations: Optional[list[Remediation]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    scores: Optional[list[Score]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    threats: Optional[list[Threat]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    title: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if hasattr(self, "acknowledgments"):
            if isinstance(self.acknowledgments, list):
                self.acknowledgments = [
                    Acknowledgment(**dict(x)) for x in self.acknowledgments
                ]

        if isinstance(self.cwe, dict):
            self.cwe = CWE(**self.cwe)

        if hasattr(self, "flags"):
            if isinstance(self.flags, list):
                self.flags = [Flag(**dict(x)) for x in self.flags]

        if hasattr(self, "ids"):
            if isinstance(self.ids, list):
                self.ids = [ID(**dict(x)) for x in self.ids]

        if hasattr(self, "involvements"):
            if isinstance(self.involvements, list):
                self.involvements = [Involvement(**dict(x)) for x in self.involvements]

        if hasattr(self, "notes"):
            if isinstance(self.notes, list):
                self.notes = [Note(**dict(x)) for x in self.notes]

        if isinstance(self.product_status, dict):
            self.product_status = ProductStatus(**self.product_status)

        if hasattr(self, "references"):
            if isinstance(self.references, list):
                self.references = [Reference(**dict(x)) for x in self.references]

        if hasattr(self, "remediations"):
            if isinstance(self.remediations, list):
                self.remediations = [Remediation(**dict(x)) for x in self.remediations]

        if hasattr(self, "scores"):
            if isinstance(self.scores, list):
                self.scores = [Score(**dict(x)) for x in self.scores]

        if hasattr(self, "threats"):
            if isinstance(self.threats, list):
                self.threats = [Threat(**dict(x)) for x in self.threats]


@dataclass_json
@dataclass
class CSAF(Validations):
    """i.a.w https://docs.oasis-open.org/csaf/csaf/v2.0/csaf_json_schema.json"""

    document: Document

    product_tree: Optional[ProductTree] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    vulnerabilities: Optional[list[Vulnerability]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def __post_init__(self):
        if isinstance(self.document, dict):
            self.document = Document(**self.document)

        if hasattr(self, "product_tree"):
            if isinstance(self.product_tree, dict):
                self.product_tree = ProductTree(**self.product_tree)

        if hasattr(self, "vulnerabilities"):
            if isinstance(self.vulnerabilities, list):
                self.vulnerabilities = [
                    Vulnerability(**dict(x)) for x in self.vulnerabilities
                ]

    @property
    def cve_id(self) -> str:
        return f"{self.document.tracking.id}"

    @property
    def publisher(self) -> str:
        return f"{self.document.publisher.name}"

    def __repr__(self):
        return f"CSAF({self.document.publisher.name}[{self.document.tracking.id}])"
