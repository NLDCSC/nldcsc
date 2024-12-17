import logging

from nldcsc.http_apis.base_class.api_base_class import ApiBaseClass
from nldcsc.loggers.app_logger import AppLogger
from nldcsc.plugins.whoisxml.objects.whois import WhoisRecord

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
