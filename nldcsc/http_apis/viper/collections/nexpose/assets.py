from typing import Literal

from nldcsc.http_apis.viper.collections.bases import EndpointCollection
from nldcsc.http_apis.viper.collections.utils import as_object
from nldcsc.http_apis.viper.objects import AsyncSearchResponse

from .objects import AssetResponse, Vulnerabilities


class AssetCollection(EndpointCollection):
    @as_object(AsyncSearchResponse)
    def create_async_search(
        self,
        page: int = 0,
        size: int = 50,
        sort: str = "id:asc",
        filters: list[dict] | None = None,
        match: Literal["all", "any"] = "all",
    ):
        resource = "assets/async_search"

        return self.call(
            self.methods.POST,
            resource,
            params={"page": page, "size": size, "sort": sort},
            json={"filters": filters or [], "match": match},
        )

    @as_object(AssetResponse)
    def get_async_search(self, async_search_id: str):
        resource = f"assets/async_search/{async_search_id}"

        return self.call(self.methods.GET, resource)

    @as_object(AsyncSearchResponse)
    def search_asset_vulnerabilities(
        self, asset_id: int, page: int = 0, size: int = 50, sort: str = "id:asc"
    ):
        resource = "asset/vulnerabilities/async_search"

        return self.call(
            self.methods.POST,
            resource,
            params={"page": page, "size": size, "sort": sort, "asset_id": asset_id},
        )

    @as_object(Vulnerabilities, transform=Vulnerabilities)
    def get_asset_vulnerabilities(self, async_search_id: str):
        resource = f"asset/vulnerabilities/async_search/{async_search_id}"

        return self.call(self.methods.GET, resource)
