import logging

import requests

from nldcsc.loggers.app_logger import AppLogger
from nldcsc.plugins.hybrid_analysis.objects import HybridAnalysisHashRecord

logging.setLoggerClass(AppLogger)


class HybridAnalysisAPI:
    def __init__(
        self,
        api_key: str,
        baseurl: str = "https://www.hybrid-analysis.com",
        api_path: str = "api/v2",
        proxies: dict = None,
        user_agent: str = "Certex",
    ):
        self.url = f"{baseurl}/{api_path}"
        self.proxies = proxies
        self.headers = {}
        self.headers["api-key"] = api_key
        self.headers["User-Agent"] = user_agent
        self.session = requests.Session()
        self.session.headers = self.headers
        self.session.proxies = proxies

    def search_hash(
        self, hash: str, get_obj: bool = False
    ) -> dict | list[HybridAnalysisHashRecord]:
        data = {
            "hash": hash,
        }
        response: list[dict] = self.session.post(
            url=f"{self.url}/search/hash",
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                **self.headers,
            },
            proxies=self.proxies,
        ).json()

        if get_obj:
            records = []
            items = []
            if isinstance(response, dict):
                items = [response]
            elif isinstance(response, list):
                items = response
            else:
                logging.getLogger(__name__).warning(
                    "Unexpected response type from HybridAnalysis API: %s",
                    type(response),
                )
                return response

            allowed_fields = set(HybridAnalysisHashRecord.__dataclass_fields__.keys())

            for record in items:
                if isinstance(record, dict):
                    filtered = {k: v for k, v in record.items() if k in allowed_fields}
                    records.append(HybridAnalysisHashRecord(**filtered))
                else:
                    logging.getLogger(__name__).warning(
                        "Skipping HybridAnalysis record with unexpected type: %s",
                        type(record),
                    )

            return records
        else:
            return response
