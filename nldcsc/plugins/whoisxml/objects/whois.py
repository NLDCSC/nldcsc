from dataclasses import dataclass
from typing import List, Optional

from dataclasses_json import dataclass_json

from nldcsc.generic.times import timestringTOtimestamp


@dataclass_json
@dataclass
class OrganisationDetails:
    name: Optional[str] = None
    organization: Optional[str] = None
    street1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postalCode: Optional[str] = None
    country: Optional[str] = None
    countryCode: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    rawText: Optional[str] = None


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
    rawText: Optional[str] = None
    hostNames: Optional[List[str]] = None
    ips: Optional[List[str]] = None


@dataclass_json
@dataclass
class MetaData:
    status: Optional[str] = None
    rawText: Optional[str] = None
    parseCode: Optional[int] = None
    dataError: Optional[str] = None
    header: Optional[str] = None
    strippedText: Optional[str] = None
    footer: Optional[str] = None
    audit: Optional[dict[str, str]] = None
    customField1Name: Optional[str] = None
    customField1Value: Optional[str] = None
    registrarName: Optional[str] = None
    registrarIANAID: Optional[str] = None
    createdDateNormalized: Optional[str] = None
    updatedDateNormalized: Optional[str] = None
    expiresDateNormalized: Optional[str] = None
    customField2Name: Optional[str] = None
    customField3Name: Optional[str] = None
    customField2Value: Optional[str] = None
    customField3Value: Optional[str] = None


@dataclass_json
@dataclass
class RegistryData(MetaData):
    domainName: Optional[str] = None
    nameServers: Optional["NameServers"] = None
    whoisServer: Optional[str] = None
    createdDate: Optional[str] = None
    updatedDate: Optional[str] = None
    expiresDate: Optional[str] = None

    def __post_init__(self):
        if self.__getattribute__("nameServers") is not None:
            self.__setattr__(
                "nameServers", NameServers(**self.__getattribute__("nameServers"))
            )


@dataclass_json
@dataclass
class WhoisRecord(MetaData):
    createdDate: Optional[str] = None
    updatedDate: Optional[str] = None
    expiresDate: Optional[str] = None
    registrant: Optional["Registrant"] = None
    administrativeContact: Optional["AdministrativeContact"] = None
    technicalContact: Optional["TechnicalContact"] = None
    domainName: Optional[str] = None
    nameServers: Optional["NameServers"] = None
    registryData: Optional["RegistryData"] = None
    domainAvailability: Optional[str] = None
    contactEmail: Optional[str] = None
    domainNameExt: Optional[str] = None
    estimatedDomainAge: Optional[int] = None
    ips: Optional[List[str]] = None

    def __post_init__(self):
        if self.__getattribute__("registrant") is not None:
            self.__setattr__(
                "registrant", Registrant(**self.__getattribute__("registrant"))
            )
        if self.__getattribute__("administrativeContact") is not None:
            self.__setattr__(
                "administrativeContact",
                AdministrativeContact(**self.__getattribute__("administrativeContact")),
            )
        if self.__getattribute__("technicalContact") is not None:
            self.__setattr__(
                "technicalContact",
                TechnicalContact(**self.__getattribute__("technicalContact")),
            )
        if self.__getattribute__("nameServers") is not None:
            self.__setattr__(
                "nameServers", NameServers(**self.__getattribute__("nameServers"))
            )
        if self.__getattribute__("registryData") is not None:
            self.__setattr__(
                "registryData", RegistryData(**self.__getattribute__("registryData"))
            )

    @property
    def domain_is_available(self):
        if (
            self.domainAvailability is not None
            and self.domainAvailability == "UNAVAILABLE"
        ):
            return False
        else:
            return True

    @property
    def get_registrar(self) -> str | None:
        return self.registrarName

    @property
    def get_created_date(self) -> int:
        if self.registryData.createdDate:
            return timestringTOtimestamp(self.registryData.createdDate)
        else:
            return 0

    @property
    def get_updated_date(self) -> int:
        if self.registryData.updatedDate:
            return timestringTOtimestamp(self.registryData.updatedDate)
        else:
            return 0

    @property
    def get_expires_date(self) -> int:
        if self.registryData.expiresDate:
            return timestringTOtimestamp(self.registryData.expiresDate)
        else:
            return 0
