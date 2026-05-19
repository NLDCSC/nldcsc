from dataclasses import dataclass, field

from dataclasses_json import DataClassJsonMixin, LetterCase, config


class NexposeDataClassConfig(DataClassJsonMixin):
    dataclass_json_config = config(letter_case=LetterCase.CAMEL)["dataclasses_json"]


@dataclass
class NexposeLink(NexposeDataClassConfig):
    deprecation: str
    href: str
    hreflang: str
    media: str
    rel: str
    title: str
    type: str


@dataclass
class NexposePage(NexposeDataClassConfig):
    number: int
    size: int
    total_pages: int
    total_resources: int


@dataclass
class NexposeAddress(NexposeDataClassConfig):
    ip: str
    mac: str


@dataclass
class NexposeConfiguration(NexposeDataClassConfig):
    name: str
    value: str


@dataclass
class NexposeDatabase(NexposeDataClassConfig):
    description: str
    id: int
    name: str


@dataclass
class NexposeFile(NexposeDataClassConfig):
    attributes: list[NexposeConfiguration]
    name: str
    size: int
    type: str


@dataclass
class NexposeHistory(NexposeDataClassConfig):
    date: str
    description: str
    scan_id: int
    type: str
    user: str
    version: int
    vulnerability_Exception_id: int


@dataclass
class NexposeID(NexposeDataClassConfig):
    id: str
    source: str


@dataclass
class NexposeCPE(NexposeDataClassConfig):
    edition: str
    language: str
    other: str
    part: str
    product: str
    sw_edition: str
    target_hw: str
    target_sw: str
    update: str
    vendor: str
    version: str
    v2_2: str = field(metadata=config(field_name="v2.2"))
    v2_3: str = field(metadata=config(field_name="v2.3"))


@dataclass
class NexposeOSFingerprint(NexposeDataClassConfig):
    architecture: str
    configurations: list[NexposeConfiguration]
    cpe: NexposeCPE
    description: str
    family: str
    id: int
    product: str
    system_name: str
    type: str
    vendor: str
    version: str


@dataclass
class NexposeAssetVulnerabilities(NexposeDataClassConfig):
    critical: int
    exploits: int
    malware_kits: int
    moderate: int
    severe: int
    total: int


@dataclass
class NexposeResource(NexposeDataClassConfig):
    addresses: list[NexposeAddress]
    assessed_for_policies: bool
    assessed_for_vulnerabilities: bool
    configurations: list[NexposeConfiguration]
    databases: list[NexposeDatabase]
    files: list[NexposeFile]
    history: list[NexposeHistory]
    host_name: str
    host_names: list[str]
    id: int
    ids: list[NexposeID]
    ip: str
    links: list[NexposeLink]
    mac: str
    os: str
    os_certainty: str
    os_fingerprint: NexposeOSFingerprint
    raw_risk_score: float
    risk_score: float
    services: list
    software: list
    type: str
    user_groups: list
    users: list
    vulnerabilities: NexposeAssetVulnerabilities


@dataclass
class NexposeAssets(NexposeDataClassConfig):
    links: list[NexposeLink]
    page: NexposePage
    resources: list[NexposeResource]
