from dataclasses import dataclass

from dataclasses_json import DataClassJsonMixin, LetterCase, config


class NexposeDataClassConfig(DataClassJsonMixin):
    dataclass_json_config = config(letter_case=LetterCase.CAMEL)["dataclasses_json"]


@dataclass
class NexposeLinks(NexposeDataClassConfig):

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
class NexposeResource(NexposeDataClassConfig): ...


@dataclass
class NexposeAssets(NexposeDataClassConfig):
    links: list[NexposeLinks]
    page: NexposePage
    resources: list[NexposeResource]
