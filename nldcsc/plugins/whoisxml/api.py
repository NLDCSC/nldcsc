import logging
from typing import List

from nldcsc.http_apis.base_class.api_base_class import ApiBaseClass
from nldcsc.loggers.app_logger import AppLogger
from nldcsc.plugins.whoisxml.objects.whois import (
    WhoisRecord,
    WhoisReverseNSRecord,
    WhoisReverseMXRecord,
    WhoisReverseIPRecord,
)

logging.setLoggerClass(AppLogger)


class WhoisXMLAPI(ApiBaseClass):
    def __init__(
        self,
        api_key: str,
        baseurl: str = "https://www.whoisxmlapi.com",
        api_path: str = "",
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

        self.set_header_field("Authorization", f"Bearer {api_key}")

    def get_whois_record(
        self, domain_name: str, get_obj: bool = False
    ) -> dict | WhoisRecord:
        """
        https://whois.whoisxmlapi.com/documentation/making-requests

        Returns the whois record for the given domain name

        {
            "createdDate": "1997-09-15T00:00:00-0700",
            "updatedDate": "2018-02-21T10:45:07-0800",
            "expiresDate": "2020-09-13T21:00:00-0700",
            "registrant": {
              "organization": "Google LLC",
              "state": "CA",
              "country": "UNITED STATES",
              "countryCode": "US",
              "rawText": "Registrant Organization: Google LLC [...]"
            },
            "administrativeContact": {
              "organization": "Google LLC",
              "state": "CA",
              "country": "UNITED STATES",
              "countryCode": "US",
              "rawText": "Admin Organization: Google LLC [...]"
            },
            "technicalContact": {
              "organization": "Google LLC",
              "state": "CA",
              "country": "UNITED STATES",
              "countryCode": "US",
              "rawText": "Tech Organization: Google LLC [...]"
            },
            "domainName": "google.com",
            "nameServers": {
              "rawText": "ns2.google.com ns3.google.com ns1.google.com ns4.google.com",
              "hostNames": [
                "ns2.google.com",
                "ns3.google.com",
                "ns1.google.com",
                "ns4.google.com"
              ],
              "ips": []
            },
            "status": "clientUpdateProhibited [...]",
            "rawText": "Domain Name: google.com [...]",
            "parseCode": 3579,
            "header": "",
            "strippedText": "Domain Name: google.com [...]",
            "footer": "",
            "audit": {
              "createdDate": "2018-10-23 15:33:41.000 UTC",
              "updatedDate": "2018-10-23 15:33:41.000 UTC"
            },
            "customField1Name": "RegistrarContactEmail",
            "customField1Value": "abusecomplaints@markmonitor.com",
            "registrarName": "MarkMonitor, Inc.",
            "registrarIANAID": "292",
            "createdDateNormalized": "1997-09-15 07:00:00 UTC",
            "updatedDateNormalized": "2018-02-21 18:45:07 UTC",
            "expiresDateNormalized": "2020-09-14 04:00:00 UTC",
            "customField2Name": "RegistrarContactPhone",
            "customField3Name": "RegistrarURL",
            "customField2Value": "+1.2083895740",
            "customField3Value": "http://www.markmonitor.com",
            "registryData": {
              "createdDate": "1997-09-15T04:00:00Z",
              "updatedDate": "2018-02-21T18:36:40Z",
              "expiresDate": "2020-09-14T04:00:00Z",
              "domainName": "google.com",
              "nameServers": {
                "rawText": "NS1.GOOGLE.COM NS2.GOOGLE.COM NS3.GOOGLE.COM NS4.GOOGLE.COM",
                "hostNames": [
                  "NS1.GOOGLE.COM",
                  "NS2.GOOGLE.COM",
                  "NS3.GOOGLE.COM",
                  "NS4.GOOGLE.COM"
                ],
                "ips": []
              },
              "status": "clientDeleteProhibited [...]",
              "rawText": "Domain Name: GOOGLE.COM [...]",
              "parseCode": 251,
              "header": "",
              "strippedText": "Domain Name: GOOGLE.COM [...]",
              "footer": "",
              "audit": {
                "createdDate": "2018-10-23 15:33:40.000 UTC",
                "updatedDate": "2018-10-23 15:33:40.000 UTC"
              },
              "customField1Name": "RegistrarContactEmail",
              "customField1Value": "abusecomplaints@markmonitor.com",
              "registrarName": "MarkMonitor Inc.",
              "registrarIANAID": "292",
              "createdDateNormalized": "1997-09-15 04:00:00 UTC",
              "updatedDateNormalized": "2018-02-21 18:36:40 UTC",
              "expiresDateNormalized": "2020-09-14 04:00:00 UTC",
              "customField2Name": "RegistrarContactPhone",
              "customField3Name": "RegistrarURL",
              "customField2Value": "+1.2083895740",
              "customField3Value": "http://www.markmonitor.com",
              "whoisServer": "whois.markmonitor.com"
            },
            "domainAvailability": "UNAVAILABLE",
            "contactEmail": "abusecomplaints@markmonitor.com",
            "domainNameExt": ".com",
            "estimatedDomainAge": 7708,
            "ips": [
              "172.217.11.174"
            ]
        }
        """
        resource = (
            f"whoisserver/WhoisService?domainName={domain_name}&outputFormat=JSON&da=1"
        )
        response: dict = self.call(method=self.methods.GET, resource=resource)
        if get_obj:
            return WhoisRecord(**response["WhoisRecord"])
        else:
            return response


class WhoisReverseNSAPI(ApiBaseClass):
    def __init__(
        self,
        api_key: str,
        baseurl: str = "https://reverse-ns.whoisxmlapi.com",
        api_path: str = "api/v1",
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
        self.api_key = api_key

    def get_domains(
        self, ns_value: str, max_queries: int = None, get_obj: bool = False
    ) -> List[WhoisReverseNSRecord]:
        """


        Finds domain names associated with a nameserver using the WhoisXML Reverse NS API.
        Args:
            ns_value (str): The nameserver value to query for associated domain names.
            max_queries (int): The maximum number of queries to run. The API returns up to 300 results per query.
            get_obj (bool, optional): If True, returns a list of WhoisReverseNSRecord objects.
                    If False, returns a list of raw dictionary results. Defaults to False.
        Returns:
            List[WhoisReverseNSRecord] or List[dict]: A list of domain names associated with the given nameserver.
                    The format depends on the value of `get_obj`.
        Notes:
            - The API is paginated, and this method handles pagination automatically.
            - If the API response contains fewer than 300 results, it assumes there are no more pages.
            - Refer to the API documentation for more details:
                    https://reverse-ns.whoisxmlapi.com/api/documentation/making-requests

        """
        page = 1
        all_results = []
        query_count = 0
        while True:
            if max_queries and query_count >= max_queries:
                break
            resource = f"?apiKey={self.api_key}&ns={ns_value}&from={page}"
            response: dict = self.call(method=self.methods.GET, resource=resource)
            query_count += 1
            if "result" not in response or not response["result"]:
                break
            all_results.extend(response["result"])
            if len(response["result"]) < 300:
                break
            page = response["result"][-1]["name"]
        if get_obj:
            return [WhoisReverseNSRecord(**record) for record in all_results]
        else:
            return all_results


class WhoisReverseMXAPI(ApiBaseClass):
    def __init__(
        self,
        api_key: str,
        baseurl: str = "https://reverse-mx.whoisxmlapi.com",
        api_path: str = "api/v1",
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
        self.api_key = api_key

    def get_domains(
        self, mx_value: str, max_queries: int = None, get_obj: bool = False
    ) -> List[WhoisReverseMXRecord]:
        """


        Finds domain names associated with a mailserver using the WhoisXML Reverse MX API.
        Args:
            mx_value (str): The mailserver value to query for associated domain names.
            max_queries (int): The maximum number of queries to run. The API returns up to 300 results per query.
            get_obj (bool, optional): If True, returns a list of WhoisReverseMXRecord objects.
                    If False, returns a list of raw dictionary results. Defaults to False.
        Returns:
            List[WhoisReverseMXRecord] or List[dict]: A list of domain names associated with the given mailserver.
                    The format depends on the value of `get_obj`.
        Notes:
            - The API is paginated, and this method handles pagination automatically.
            - If the API response contains fewer than 300 results, it assumes there are no more pages.
            - Refer to the API documentation for more details:
                    https://reverse-mx.whoisxmlapi.com/api/documentation/making-requests

        """
        page = 1
        all_results = []
        query_count = 0
        while True:
            if max_queries and query_count >= max_queries:
                break
            resource = f"?apiKey={self.api_key}&mx={mx_value}&from={page}"
            response: dict = self.call(method=self.methods.GET, resource=resource)
            query_count += 1
            if "result" not in response or not response["result"]:
                break
            all_results.extend(response["result"])
            if len(response["result"]) < 300:
                break
            page = response["result"][-1]["name"]
        if get_obj:
            return [WhoisReverseMXRecord(**record) for record in all_results]
        else:
            return all_results


class WhoisReverseIPAPI(ApiBaseClass):
    def __init__(
        self,
        api_key: str,
        baseurl: str = "https://reverse-ip.whoisxmlapi.com",
        api_path: str = "api/v1",
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
        self.api_key = api_key

    def get_domains(
        self, ip_value: str, max_queries: int = None, get_obj: bool = False
    ) -> List[WhoisReverseIPRecord]:
        """


        Finds domain names associated with an ip using the WhoisXML Reverse IP API.
        Args:
            ip_value (str): The ip value to query for associated domain names.
            max_queries (int): The maximum number of queries to run. The API returns up to 300 results per query.
            get_obj (bool, optional): If True, returns a list of WhoisReverseIPRecord objects.
                    If False, returns a list of raw dictionary results. Defaults to False.
        Returns:
            List[WhoisReverseIPRecord] or List[dict]: A list of domain names associated with the given ip.
                    The format depends on the value of `get_obj`.
        Notes:
            - The API is paginated, and this method handles pagination automatically.
            - If the API response contains fewer than 300 results, it assumes there are no more pages.
            - Refer to the API documentation for more details:
                    https://reverse-ip.whoisxmlapi.com/api/documentation/making-requests
        """
        page = 1
        all_results = []
        query_count = 0
        while True:
            if max_queries and query_count >= max_queries:
                break
            resource = f"?apiKey={self.api_key}&ip={ip_value}&from={page}"
            response: dict = self.call(method=self.methods.GET, resource=resource)
            query_count += 1
            if "result" not in response or not response["result"]:
                break
            all_results.extend(response["result"])
            if len(response["result"]) < 300:
                break
            page = response["result"][-1]["name"]
        if get_obj:
            return [WhoisReverseIPRecord(**record) for record in all_results]
        else:
            return all_results
