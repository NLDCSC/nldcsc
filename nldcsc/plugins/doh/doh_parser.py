import collections
import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from dataclasses_json import config as json_config
from dataclasses_json import dataclass_json
from httpx import Response
from netaddr.ip import IPAddress
from nldcsc.generic.utils import exclude_optional_dict, reverse_from_named_tuple
from nldcsc.loggers.app_logger import AppLogger

from nldcsc.plugins.doh.doh_requester import DOHRequester, q_types

logging.setLoggerClass(AppLogger)

status_types = collections.namedtuple(
    "status_types",
    ["NOERROR", "FORMERR", "SERVFAIL", "NXDOMAIN", "NOTIMP", "REFUSED"],
)(0, 1, 2, 3, 4, 5)


def reverse_pointer_ip(ptr_address: str) -> str | None:
    """
    Method to reverse the reverse dns lookup address

    Args:
        ptr_address: reverse DNS lookup address

    Returns:
        original IP or None
    """
    ipv4_def = ".in-addr.arpa"
    ipv6_def = ".ip6.arpa"

    if ipv4_def in ptr_address:
        address = ptr_address.replace(ipv4_def, "")
        reverse_octets = address.split(".")[::-1]
        return ".".join(reverse_octets)

    if ipv6_def in ptr_address:
        address = ptr_address.replace(ipv6_def, "")
        reverse_string = address.replace(".", "")[::-1]
        full_ipv6_string = ":".join(
            reverse_string[i : i + 4] for i in range(0, len(reverse_string), 4)
        )
        ipv6_address = IPAddress(full_ipv6_string)
        return str(ipv6_address)

    return None


# noinspection PyClassHasNoInitInspection
@dataclass_json
@dataclass
class QuestionData:
    name: str
    type: int
    original_ip: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    @property
    def s_type(self) -> str:
        return reverse_from_named_tuple(q_types, self.type)


# noinspection PyClassHasNoInitInspection
@dataclass_json
@dataclass
class AnswerData:
    name: str
    type: int
    TTL: int
    data: str

    @property
    def s_type(self) -> str:
        return reverse_from_named_tuple(q_types, self.type)


# noinspection PyClassHasNoInitInspection
@dataclass_json
@dataclass
class Request:
    Status: int
    TC: bool
    RD: bool
    RA: bool
    AD: bool
    CD: bool
    Question: List[QuestionData]
    Answer: Optional[List[AnswerData]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    Authority: Optional[List[AnswerData]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    Comment: Optional[List[str]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    @property
    def s_status(self) -> str:
        return reverse_from_named_tuple(status_types, self.Status)

    @property
    def request_ok(self) -> bool:
        return self.Status == status_types.NOERROR

    @property
    def domain_exists(self) -> bool:
        return (
            not self.Status == status_types.NXDOMAIN
            and self.Status == status_types.NOERROR
        )

    @property
    def reverse_data_lookups(self) -> List[str]:
        if self.Status == status_types.NOERROR:
            if self.Answer is not None and len(self.Answer) > 0:
                return [
                    x.data for x in self.Answer if x.type in [q_types.A, q_types.AAAA]
                ]

        return []


class DohParser(object):
    def __init__(self):
        """
        Create new instance of DohParser
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.doh_requester = DOHRequester("https://1.1.1.1")

    async def make_requests(
        self, workload: dict[int | str, List[str]]
    ) -> List[Response]:
        """
        Method to make DOH requests using the get_bulk_domains method of the DohRequester class

        Args:
            workload: a dictionary as dictated by get_bulk_domains method of the DohRequester class

        Returns:
            A list of `Response` objects
        """
        data = await self.doh_requester.get_bulk_domains(workload=workload)
        return data

    def parse_responses(self, responses: List[Response]) -> List[Request]:
        """
        Method to parse the responses returned from the get_bulk_domains method of the DohRequester class and parse
        these into `Request` objects

        Args:
            responses: A list of `Response` objects

        Returns:
            A list of `Request` objects
        """
        r_list = []
        for response in responses:
            if response.status_code == 200:
                try:
                    data = json.loads(response.content.decode("utf-8"))
                    if isinstance(data, dict):
                        if "Question" in data:
                            q_list = [
                                QuestionData(
                                    **x,
                                    original_ip=reverse_pointer_ip(x["name"]),
                                )
                                for x in data["Question"]
                            ]
                            data["Question"] = q_list
                        if "Answer" in data:
                            a_list = [AnswerData(**x) for x in data["Answer"]]
                            data["Answer"] = a_list
                        if "Authority" in data:
                            a_list = [AnswerData(**x) for x in data["Authority"]]
                            data["Authority"] = a_list

                        r_list.append(Request(**data))
                    else:
                        raise ValueError
                except TypeError:
                    self.logger.warning(
                        f"Response {response.content} yielded fields that could not be parsed..."
                    )
                    continue
                except UnicodeDecodeError:
                    self.logger.warning(f"Couldn't decode response: {response.content}")
                    continue
                except ValueError:
                    self.logger.warning(
                        f"Unexpected type in response: {response.content}"
                    )
                    continue
                except Exception:
                    self.logger.warning(
                        f"Uncaught error while parsing response: {response.content}"
                    )
                    continue
        return r_list

    async def request_and_parse(
        self, workload: dict[int | str, List[str]]
    ) -> dict[str, List[dict[str, str | int | List[dict[str, str | int]]]]]:
        query_data = await self.make_requests(workload=workload)

        # forward dns queries
        query_request_data = self.parse_responses(query_data)

        # reverse lookups
        reverse_lookups = []
        for response in query_request_data:
            reverse_lookups.extend(response.reverse_data_lookups)
        reverse_data = await self.make_requests(
            workload={q_types.PTR: list(set(reverse_lookups))}
        )

        reverse_request_data = self.parse_responses(reverse_data)

        ret_dict = {
            "forward_requests": [x.to_dict() for x in query_request_data],
            "reverse_requests": [x.to_dict() for x in reverse_request_data],
        }

        return ret_dict

    def __repr__(self):
        return "<< DohParser >>"
