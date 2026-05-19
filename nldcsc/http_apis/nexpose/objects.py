from dataclasses import dataclass, field

from dataclasses_json import DataClassJsonMixin, LetterCase, config, global_config
from enum import StrEnum, Enum, auto


def encode_as_string(e: Enum):
    """
    decorator to be used and encode the enum back to its str value

    Args:
        e (Enum): enum to register a string encoder for
    """
    global_config.encoders[e] = str


@encode_as_string
class NexposeHistoryType(StrEnum):
    ASSET_IMPORT = "ASSET-IMPORT"
    EXTERNAL_IMPORT = "EXTERNAL-IMPORT"
    EXTERNAL_IMPORT_APPSPIDER = "EXTERNAL-IMPORT-APPSPIDER"
    SCAN = "SCAN"
    AGENT_IMPORT = "AGENT-IMPORT"
    ACTIVE_SYNC = "ACTIVE-SYNC"
    SCAN_LOG_IMPORT = "SCAN-LOG-IMPORT"
    VULNERABILITY_EXCEPTION_APPLIED = "VULNERABILITY_EXCEPTION_APPLIED"
    VULNERABILITY_EXCEPTION_UNAPPLIED = "VULNERABILITY_EXCEPTION_UNAPPLIED"


@encode_as_string
class NexposeFileType(StrEnum):
    FILE = auto()
    DIRECTORY = auto()


@encode_as_string
class NexposeAssetType(StrEnum):
    UNKNOWN = auto()
    GUEST = auto()
    HYPERVISOR = auto()
    PHYSICAL = auto()
    MOBILE = auto()


@encode_as_string
class NexposeHostNameSource(StrEnum):
    USER = auto()
    DNS = auto()
    NETBIOS = auto()
    DCE = auto()
    EPSEC = auto()
    LDAP = auto()
    OTHER = auto()


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
    type: NexposeFileType


@dataclass
class NexposeHistory(NexposeDataClassConfig):
    date: str
    description: str
    scan_id: int
    type: NexposeHistoryType
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
class NexposeUser(NexposeDataClassConfig):
    fullname: str
    id: int
    name: str


@dataclass
class NexposeUserGroup(NexposeDataClassConfig):
    id: int
    name: str


@dataclass
class NexposeSoftware(NexposeDataClassConfig):
    configurations: list[NexposeConfiguration]
    cpe: NexposeCPE
    description: str
    family: str
    id: int
    product: str
    type: str
    vendor: str
    version: str


@dataclass
class NexposeWebPage(NexposeDataClassConfig):
    link_type: str
    path: str
    response: int


@dataclass
class NexposeWebApplication(NexposeDataClassConfig):
    id: int
    pages: list[NexposeWebPage]
    root: str
    virtual_host: str


@dataclass
class NexposeService(NexposeDataClassConfig):
    configurations: list[NexposeConfiguration]
    databases: list[NexposeDatabase]
    family: str
    links: list[NexposeLink]
    name: str
    nic: str
    port: int
    product: str
    protocol: str
    user_groups: list[NexposeUserGroup]
    users: list[NexposeUser]
    vendor: str
    version: str
    web_applications: list[NexposeWebApplication]


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
    services: list[NexposeService]
    software: list[NexposeSoftware]
    type: NexposeAssetType
    user_groups: list[NexposeUserGroup]
    users: list[NexposeUser]
    vulnerabilities: NexposeAssetVulnerabilities


@dataclass
class NexposeAssets(NexposeDataClassConfig):
    links: list[NexposeLink]
    page: NexposePage
    resources: list[NexposeResource]
