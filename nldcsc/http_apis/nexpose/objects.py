from dataclasses import dataclass, field
from typing import Any, Optional, Type, TypedDict, NotRequired

from dataclasses_json import DataClassJsonMixin, LetterCase, config, global_config
from enum import StrEnum, Enum, auto


def encode_as_string(e: Type[Enum]):
    """
    decorator to be used and encode the enum back to its str value

    Args:
        e (Enum): enum to register a string encoder for
    """
    global_config.encoders[e] = str

    return e


class NexposeFilterOperator(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.lower().replace("_", "-")

    IN = auto()
    IS = auto()
    IS_NOT = auto()
    STARTS_WITH = auto()
    ENDS_WITH = auto()
    CONTAINS = auto()
    DOES_NOT_CONTAIN = auto()
    IS_LIKE = auto()
    NOT_LIKE = auto()
    ARE = auto()
    IS_GREATER_THAN = auto()
    IS_LESS_THAN = auto()
    IS_APPLIED = auto()
    IS_NOT_APPLIED = auto()
    IS_EMPTY = auto()
    IS_NOT_EMPTY = auto()
    IN_RANGE = auto()
    NOT_IN_RANGE = auto()
    IS_ON_OR_BEFORE = auto()
    IS_ON_OR_AFTER = auto()
    IS_BETWEEN = auto()
    IS_EARLIER_THAN = auto()
    IS_WITHIN_THE_LAST = auto()
    INCLUDES = auto()
    DOES_NOT_INCLUDE = auto()


class NexposeSearchMatch(StrEnum):
    ANY = auto()
    ALL = auto()


class NexposeSortingDirection(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name

    ASC = auto()
    DESC = auto()


@encode_as_string
class NexposeVulnerabilityStatus(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.lower().replace("_", "-")

    VULNERABLE = auto()
    INVULNERABLE = auto()
    NO_RESULTS = auto()


@encode_as_string
class NexposeResultStatus(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.lower().replace("_", "-")

    UNKNOWN = auto()
    NOT_VULNERABLE = auto()
    VULNERABLE = auto()
    VULNERABLE_VERSION = auto()
    VULNERABLE_POTENTIAL = auto()
    VULNERABLE_WITH_EXCEPTION_APPLIED = auto()
    VULNERABLE_VERSION_WITH_EXCEPTION_APPLIED = auto()
    VULNERABLE_POTENTIAL_WITH_EXCEPTION_APPLIED = auto()


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


@encode_as_string
class NexposeProtocol(StrEnum):
    IP = auto()
    ICMP = auto()
    IGMP = auto()
    GGP = auto()
    TCP = auto()
    PUP = auto()
    UDP = auto()
    IDP = auto()
    ESP = auto()
    ND = auto()
    RAW = auto()


@encode_as_string
class NexposeLinkType(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.lower().replace("_", "-")

    SEED = auto()
    ROBOTS = auto()
    PDF = auto()
    CSS = auto()
    IMPLIED_DIR = auto()
    RSS = auto()
    REDIRECTION = auto()
    SITEMAP = auto()
    BACKUP = auto()
    VCK_REWRITE = auto()
    NON_REF_GUESS = auto()
    SOFT_404 = auto()
    HTML_REF = auto()
    JS_STRING = auto()
    QUERY_PARAM = auto()


class NexposeFilter(TypedDict):
    # https://help.rapid7.com/insightvm/en-us/api/index.html#section/Overview/Responses

    field: str
    operator: NexposeFilterOperator
    value: NotRequired[Any]
    lower: NotRequired[Any]
    upper: NotRequired[Any]


class NexposeDataClassConfig(DataClassJsonMixin):
    dataclass_json_config = config(letter_case=LetterCase.CAMEL)["dataclasses_json"]


@dataclass
class NexposeLink(NexposeDataClassConfig):
    deprecation: Optional[str] = None
    href: Optional[str] = None
    hreflang: Optional[str] = None
    media: Optional[str] = None
    rel: Optional[str] = None
    title: Optional[str] = None
    type: Optional[str] = None


@dataclass
class NexposePage(NexposeDataClassConfig):
    number: Optional[int] = None
    size: Optional[int] = None
    total_pages: Optional[int] = None
    total_resources: Optional[int] = None


@dataclass
class NexposeAddress(NexposeDataClassConfig):
    ip: Optional[str] = None
    mac: Optional[str] = None


@dataclass
class NexposeConfiguration(NexposeDataClassConfig):
    name: Optional[str] = None
    value: Optional[str] = None


@dataclass
class NexposeDatabase(NexposeDataClassConfig):
    description: Optional[str] = None
    id: Optional[int] = None
    name: Optional[str] = None


@dataclass
class NexposeFile(NexposeDataClassConfig):
    attributes: list[NexposeConfiguration] = field(default_factory=list)
    name: Optional[str] = None
    size: Optional[int] = None
    type: Optional[NexposeFileType] = None


@dataclass
class NexposeHistory(NexposeDataClassConfig):
    date: Optional[str] = None
    description: Optional[str] = None
    scan_id: Optional[int] = None
    type: Optional[NexposeHistoryType] = None
    user: Optional[str] = None
    version: Optional[int] = None
    vulnerability_Exception_id: Optional[int] = None


@dataclass
class NexposeID(NexposeDataClassConfig):
    id: Optional[str] = None
    source: Optional[str] = None


@dataclass
class NexposeCPE(NexposeDataClassConfig):
    edition: Optional[str] = None
    language: Optional[str] = None
    other: Optional[str] = None
    part: Optional[str] = None
    product: Optional[str] = None
    sw_edition: Optional[str] = None
    target_hw: Optional[str] = None
    target_sw: Optional[str] = None
    update: Optional[str] = None
    vendor: Optional[str] = None
    version: Optional[str] = None
    v2_2: Optional[str] = field(metadata=config(field_name="v2.2"), default=None)
    v2_3: Optional[str] = field(metadata=config(field_name="v2.3"), default=None)


@dataclass
class NexposeOSFingerprint(NexposeDataClassConfig):
    architecture: Optional[str] = None
    configurations: Optional[list[NexposeConfiguration]] = field(default_factory=list)
    cpe: Optional[NexposeCPE] = None
    description: Optional[str] = None
    family: Optional[str] = None
    id: Optional[int] = None
    product: Optional[str] = None
    system_name: Optional[str] = None
    type: Optional[str] = None
    vendor: Optional[str] = None
    version: Optional[str] = None


@dataclass
class NexposeAssetVulnerabilities(NexposeDataClassConfig):
    critical: Optional[int] = None
    exploits: Optional[int] = None
    malware_kits: Optional[int] = None
    moderate: Optional[int] = None
    severe: Optional[int] = None
    total: Optional[int] = None


@dataclass
class NexposeUser(NexposeDataClassConfig):
    fullname: Optional[str] = None
    id: Optional[int] = None
    name: Optional[str] = None


@dataclass
class NexposeUserGroup(NexposeDataClassConfig):
    id: Optional[int] = None
    name: Optional[str] = None


@dataclass
class NexposeSoftware(NexposeDataClassConfig):
    configurations: Optional[list[NexposeConfiguration]] = field(default_factory=list)
    cpe: Optional[NexposeCPE] = None
    description: Optional[str] = None
    family: Optional[str] = None
    id: Optional[int] = None
    product: Optional[str] = None
    type: Optional[str] = None
    vendor: Optional[str] = None
    version: Optional[str] = None


@dataclass
class NexposeWebPage(NexposeDataClassConfig):
    link_type: Optional[NexposeLinkType] = None
    path: Optional[str] = None
    response: Optional[int] = None


@dataclass
class NexposeWebApplication(NexposeDataClassConfig):
    id: Optional[int] = None
    pages: Optional[list[NexposeWebPage]] = field(default_factory=list)
    root: Optional[str] = None
    virtual_host: Optional[str] = None


@dataclass
class NexposeService(NexposeDataClassConfig):
    configurations: Optional[list[NexposeConfiguration]] = field(default_factory=list)
    databases: Optional[list[NexposeDatabase]] = field(default_factory=list)
    family: Optional[str] = None
    links: Optional[list[NexposeLink]] = field(default_factory=list)
    name: Optional[str] = None
    nic: Optional[str] = None
    port: Optional[int] = None
    product: Optional[str] = None
    protocol: Optional[NexposeProtocol] = None
    user_groups: Optional[list[NexposeUserGroup]] = field(default_factory=list)
    users: Optional[list[NexposeUser]] = field(default_factory=list)
    vendor: Optional[str] = None
    version: Optional[str] = None
    web_applications: Optional[list[NexposeWebApplication]] = field(
        default_factory=list
    )


@dataclass
class NexposeResource(NexposeDataClassConfig):
    addresses: Optional[list[NexposeAddress]] = field(default_factory=list)
    assessed_for_policies: Optional[bool] = None
    assessed_for_vulnerabilities: Optional[bool] = None
    configurations: Optional[list[NexposeConfiguration]] = field(default_factory=list)
    databases: Optional[list[NexposeDatabase]] = field(default_factory=list)
    files: Optional[list[NexposeFile]] = field(default_factory=list)
    history: Optional[list[NexposeHistory]] = field(default_factory=list)
    host_name: Optional[str] = None
    host_names: Optional[list[str]] = field(default_factory=list)
    id: Optional[int] = None
    ids: Optional[list[NexposeID]] = field(default_factory=list)
    ip: Optional[str] = None
    links: Optional[list[NexposeLink]] = field(default_factory=list)
    mac: Optional[str] = None
    os: Optional[str] = None
    os_certainty: Optional[str] = None
    os_fingerprint: Optional[NexposeOSFingerprint] = None
    raw_risk_score: Optional[float] = None
    risk_score: Optional[float] = None
    services: Optional[list[NexposeService]] = field(default_factory=list)
    software: Optional[list[NexposeSoftware]] = field(default_factory=list)
    type: Optional[NexposeAssetType] = None
    user_groups: Optional[list[NexposeUserGroup]] = field(default_factory=list)
    users: Optional[list[NexposeUser]] = field(default_factory=list)
    vulnerabilities: Optional[NexposeAssetVulnerabilities] = None


@dataclass
class NexposeResult(NexposeDataClassConfig):
    check_id: Optional[str] = None
    exceptions: Optional[list[int]] = field(default_factory=list)
    key: Optional[str] = None
    links: Optional[list[NexposeLink]] = field(default_factory=list)
    port: Optional[int] = None
    proof: Optional[str] = None
    protocol: Optional[NexposeProtocol] = None
    reintroduced: Optional[str] = None
    since: Optional[str] = None
    status: Optional[NexposeResultStatus] = None


@dataclass
class NexposeVulnerability(NexposeDataClassConfig):
    id: str
    instances: int
    links: list[NexposeLink]
    status: NexposeVulnerabilityStatus
    results: Optional[list[NexposeResult]] = field(default_factory=list)
    since: Optional[str] = None


@dataclass
class NexposeAssets(NexposeDataClassConfig):
    links: list[NexposeLink]
    page: NexposePage
    resources: list[NexposeResource]


@dataclass
class NexposeAssetVulnerabilities(NexposeDataClassConfig):
    links: list[NexposeLink]
    page: NexposePage
    resources: list[NexposeVulnerability]
