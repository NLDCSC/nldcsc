from nldcsc.http_apis.viper.collections.bases import EndpointCollection
from nldcsc.http_apis.viper.collections.utils import as_object
from nldcsc.http_apis.viper.objects import AsyncSearchResponse

from .objects import Solutions, Vulnerabilities


class VulnerabilityDocument(EndpointCollection, prefix="vulnerability"):
    @as_object(AsyncSearchResponse)
    def create_async_search(self, vulnerability_id: str):
        resource = "async_search"

        return self.call(
            self.methods.POST, resource, params={"vulnerability_id": vulnerability_id}
        )

    @as_object(Vulnerabilities, transform=Vulnerabilities)
    def get_async_search(self, async_search_id: str):
        resource = f"async_search/{async_search_id}"

        return self.call(self.methods.GET, resource)

    @as_object(AsyncSearchResponse)
    def search_vulnerability_solutions(self, vulnerability_id: str):
        resource = "solutions/async_search"

        return self.call(
            self.methods.POST, resource, params={"vulnerability_id": vulnerability_id}
        )

    @as_object(Solutions, transform=Solutions)
    def get_vulnerability_solutions(self, async_search_id: str):
        resource = f"solutions/async_search/{async_search_id}"

        return self.call(self.methods.GET, resource)


class VulnerabilityCollection(EndpointCollection, prefix="vulnerabilities"):
    @as_object(AsyncSearchResponse)
    def create_async_search(self):
        return self.call(self.methods.POST, "async_search")

    @as_object(Vulnerabilities, transform=Vulnerabilities)
    def get_async_search(self, async_search_id: str):
        return self.call(self.methods.GET, f"async_search/{async_search_id}")
