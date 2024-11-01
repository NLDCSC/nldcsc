import collections
from ipaddress import ip_address
from typing import List

from httpx import Response
from nldcsc.httpx_apis.base_class.httpx_base_class import HttpxBaseClass

q_types = collections.namedtuple(
    "q_types", ["A", "NS", "CNAME", "SOA", "PTR", "MX", "TXT", "AAAA"]
)(1, 2, 5, 6, 12, 15, 16, 28)


class DOHRequester(HttpxBaseClass):
    def __init__(
        self,
        baseurl: str,
        api_path: str = None,
        proxies: dict = None,
        user_agent: str = "Certex",
        **kwargs,
    ):
        super().__init__(
            baseurl=baseurl,
            api_path=api_path,
            proxies=proxies,
            user_agent=user_agent,
            **kwargs,
        )

        self.clear_headers()
        self.set_header_field("accept", "application/dns-json")

    @staticmethod
    def _convert_to_reverse_format(ipaddress: str) -> str:
        """
        Convert an IP address to its reverse DNS format.

        Parameters:
            ipaddress: The IP address to convert.

        Returns:
            str: The IP address in reverse DNS format.
        """
        return ip_address(ipaddress).reverse_pointer

    async def get_domain_list_by_type(
        self, domains: List[str], dns_type: int | str = 1  # A record
    ) -> List[Response]:
        """
        Get the list of domains with specified dns type.

        Args:
            domains: list of domain names
            dns_type: https://www.iana.org/assignments/dns-parameters/dns-parameters.xhtml#dns-parameters-4 or as
                      string representation: 'A', 'NS', 'CNAME', 'SOA', 'PTR', 'MX', 'TXT', 'AAAA'

        Returns:
            List of `Response` objects
        """
        if isinstance(dns_type, str):
            try:
                dns_type = getattr(q_types, dns_type)
            except AttributeError:
                self.logger.warning(
                    f"Requesting a dns type ({dns_type}) which is not in the q_types tuple; passing requested int"
                )
                pass

        if dns_type == q_types.PTR:
            domains = [self._convert_to_reverse_format(x) for x in domains]

        resources = [f"dns-query?name={each}&type={dns_type}" for each in domains]
        data = await self.a_call(self.methods.GET, resources=resources)
        return data

    async def get_bulk_domains(
        self, workload: dict[int | str, List[str]]
    ) -> List[Response]:
        """
        Get the list of domains with specified workload.

        Args:
            workload: dictionary with qtype as key (string or int representation, or '*' to query for all q_type) and
                      a list of domain names as value.

        Returns:
            List of `Response` objects
        """
        resources = []
        query_all_types = False

        for qtype, domain_list in workload.items():
            if isinstance(qtype, str):
                if qtype == "*":
                    query_all_types = True
                    #  since we are querying all types; create a set of domain_list to filter out double entries
                    domain_list = list(set(domain_list))
                else:
                    try:
                        qtype = getattr(q_types, qtype)
                    except AttributeError:
                        self.logger.warning(
                            f"Requesting a dns type ({qtype}) which is not in the q_types tuple; passing requested int"
                        )
                        pass

            if qtype == q_types.PTR and not query_all_types:
                domain_list = [self._convert_to_reverse_format(x) for x in domain_list]

            for domain in domain_list:
                if query_all_types:
                    if len(domain.split(".")) == 2:
                        q_type_list = [
                            x
                            for x in q_types.__dir__()
                            if not x.startswith("_")
                            and x not in ["index", "count"]
                            and x != "PTR"
                        ]
                    else:
                        q_type_list = ["A", "AAAA", "CNAME", "TXT"]

                    for q_type in q_type_list:
                        resources.append(
                            f"dns-query?name={domain}&type={getattr(q_types, q_type)}"
                        )
                else:
                    resources.append(f"dns-query?name={domain}&type={qtype}")
        data = await self.a_call(self.methods.GET, resources=resources)
        return data

    async def get_reverse_lookups(self, ips: List[str]) -> List[Response]:
        """
        Get the list of reverse DNS lookups.

        Args:
            ips: list of IP addresses to lookup

        Returns:
            List of `Response` objects
        """
        resources = [
            f"dns-query?name={self._convert_to_reverse_format(each)}&type=PTR"
            for each in ips
        ]
        data = await self.a_call(self.methods.GET, resources=resources)
        return data
