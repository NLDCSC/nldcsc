from dataclasses import dataclass
from typing import List

from dataclasses_json import dataclass_json

from nldcsc.generic.times import timestringTOtimestamp


@dataclass_json
@dataclass
class OrganisationDetails:
    organization: str
    state: str
    country: str
    countryCode: str
    rawText: str


@dataclass_json
@dataclass
class Registrant(OrganisationDetails): ...


@dataclass_json
@dataclass
class AdministrativeContact(OrganisationDetails): ...


@dataclass_json
@dataclass
class TechnicalContact(OrganisationDetails): ...


@dataclass_json
@dataclass
class NameServers:
    rawText: str
    hostNames: List[str]
    ips: List[str]


@dataclass_json
@dataclass
class MetaData:
    status: str
    rawText: str
    parseCode: int
    header: str
    strippedText: str
    footer: str
    audit: dict[str, str]
    customField1Name: str
    customField1Value: str
    registrarName: str
    registrarIANAID: str
    createdDateNormalized: str
    updatedDateNormalized: str
    expiresDateNormalized: str
    customField2Name: str
    customField3Name: str
    customField2Value: str
    customField3Value: str


@dataclass_json
@dataclass
class RegistryData(MetaData):
    domainName: str
    nameServers: NameServers
    whoisServer: str
    createdDate: str | int = 0
    updatedDate: str | int = 0
    expiresDate: str | int = 0

    def __post_init__(self):
        self.__setattr__(
            "nameServers", NameServers(**self.__getattribute__("nameServers"))
        )


@dataclass_json
@dataclass
class WhoisRecord(MetaData):
    createdDate: str
    updatedDate: str
    expiresDate: str
    registrant: Registrant
    administrativeContact: AdministrativeContact
    technicalContact: TechnicalContact
    domainName: str
    nameServers: NameServers
    registryData: RegistryData
    domainAvailability: str
    contactEmail: str
    domainNameExt: str
    estimatedDomainAge: int
    ips: List[str]

    def __post_init__(self):
        self.__setattr__(
            "registrant", Registrant(**self.__getattribute__("registrant"))
        )
        self.__setattr__(
            "administrativeContact",
            AdministrativeContact(**self.__getattribute__("administrativeContact")),
        )
        self.__setattr__(
            "technicalContact",
            TechnicalContact(**self.__getattribute__("technicalContact")),
        )
        self.__setattr__(
            "nameServers", NameServers(**self.__getattribute__("nameServers"))
        )
        self.__setattr__(
            "registryData", RegistryData(**self.__getattribute__("registryData"))
        )

    @property
    def domain_is_available(self):
        if self.domainAvailability == "UNAVAILABLE":
            return False
        else:
            return True

    @property
    def get_registrar(self) -> str:
        return self.registrarName

    @property
    def get_created_date(self) -> int:
        return timestringTOtimestamp(self.registryData.createdDate)

    @property
    def get_updated_date(self) -> int:
        return timestringTOtimestamp(self.registryData.updatedDate)

    @property
    def get_expires_date(self) -> int:
        return timestringTOtimestamp(self.registryData.expiresDate)
