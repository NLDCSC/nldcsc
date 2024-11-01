import aiohttp
import asyncio
import json
import logging
import os

from netaddr import IPAddress
from netaddr.core import AddrFormatError
from nldcsc.http_apis.base_class.api_base_class import ApiBaseClass
from nldcsc.loggers.app_logger import AppLogger
from typing import List

logging.setLoggerClass(AppLogger)


class GeoIp(ApiBaseClass):
    def __init__(
        self,
        baseurl: str = "https://api.ipgeolocation.io",
        api_path: str = "ipgeo",
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

        self.logger = logging.getLogger(self.__class__.__name__)

        enabled = os.getenv("IPGEOLOCATION_ENABLE", False)
        api_key = os.getenv("IPGEOLOCATION_API_KEY", None)

        if enabled and api_key is not None:
            self.api_key = api_key
        else:
            raise ValueError(
                "IPGEOLOCATION_API_KEY must be set when ENABLE_IPGEOLOCATION is true!"
            )

    @staticmethod
    def is_valid_ip(address: str) -> bool:
        try:
            IPAddress(address)
            return True
        except AddrFormatError:
            return False

    def get_geo_for_ip(self, ip_address):
        """
        Method for retrieving a single ip address

        :param ip_address: Ip address to retrieve geo info of
        :type ip_address: str
        :return: Geo Ip Information
        :rtype: dict
        """
        # validate IP address
        if not (self.is_valid_ip(ip_address)):
            return AttributeError("Wrong ip address format...")

        resource = f"?apiKey={self.api_key}&ip={ip_address}&fields=geo,isp,organization"

        return self.call("GET", resource=resource)

    def get_country_flag(
        self, ip_address: str = None, country_code2: str = None
    ) -> bytes:
        if ip_address is None and country_code2 is None:
            raise ValueError("Either ip_address or country_code2 must be set!")

        resource = f"static/flags/<<COUNTRY_CODE2>>_64.png"

        if ip_address is not None:
            try:
                data = self.get_geo_for_ip(ip_address=ip_address)
                if "country_code2" in data:
                    resource = resource.replace(
                        "<<COUNTRY_CODE2>>", data["country_code2"].lower()
                    )
            except AttributeError:
                raise

        if country_code2 is not None:
            resource = resource.replace("<<COUNTRY_CODE2>>", country_code2.lower())

        image_url_resource = (
            self._build_url(resource)
            .replace(self.api_path + "/", "")
            .replace("api.", "")
        )

        with self.get_session() as session:
            pic_bytes = session.get(image_url_resource).content

        return pic_bytes

    def get_geo_for_ip_list(self, ip_address_list):
        """
        Method for retrieving a list with ip addresses

        :param ip_address_list: List with ip addresses to retrieve geo info of
        :type ip_address_list: list
        :return: A list with dictionaries of Geo Ip Information
        :rtype: list
        """

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(self.fetch_all(ip_address_list, loop))

        return results

    async def fetch(self, session, url):
        try:
            async with session.get(url) as response:
                data = await response.content.read()
                data = json.loads(data)
                return {data["ip"]: data}
        except KeyError:
            if "message" in data:
                self.logger.error(f"{data['message']}")
            else:
                raise
        except Exception as e:
            self.logger.exception(e)
            return {"ERROR": f"Error getting {url} data...."}

    async def fetch_all(self, ips, loop):
        sem = asyncio.Semaphore(100)
        async with sem:
            async with aiohttp.ClientSession(
                loop=loop, headers=self.headers
            ) as session:
                results = await asyncio.gather(
                    *[
                        self.fetch(
                            session,
                            f"{self._build_url(resource=f'?apiKey={self.api_key}&ip={ip}&fields=geo,isp,organization')}",
                        )
                        for ip in ips
                        if (self.is_valid_ip(ip))
                    ],
                    return_exceptions=True,
                )
                return results


class TooManyIPAddressesException(Exception):
    """Exception raised when the IP address list exceeds the maximum limit."""

    pass


class GeoIpPaid(GeoIp):
    def __init__(
        self,
        baseurl: str = "https://api.ipgeolocation.io",
        api_path: str = "ipgeo-bulk",
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

    def get_geo_for_ip_bulk(self, ip_address_list: List[str]):
        """
        Method for retrieving multiple ip addresses (max 50 at once)

        :param ip_address_list: Ip address list to retrieve geo info for
        :type ip_address_list: List[str]
        :return: List of Geo Ip Information
        :rtype: List[dict]
        :raises: AttributeError: If any ip is invalid
        :raises: TooManyIPAddressesException: If the number of provided ips is more than 50
        """
        # validate IP addresses
        for ip in ip_address_list:
            if not self.is_valid_ip(ip):
                raise AttributeError(f"Wrong IP address format found in list: {ip}")
        if len(ip_address_list) > 50:
            raise TooManyIPAddressesException(
                f"The IP address list length is {len(ip_address_list)}, which exceeds the maximum allowed limit of 50. "
                "Please provide a list with 50 or fewer IP addresses."
            )
        resource = f"?apiKey={self.api_key}"
        data = {"ips": ip_address_list}

        return self.call("POST", resource=resource, data=data)
