from nldcsc.http_apis.viper.collections.bases import EndpointCollection
from nldcsc.http_apis.viper.collections.utils import as_object
from nldcsc.http_apis.viper.objects import AsyncSearchResponse

from .objects import Solutions, Vulnerabilities


class VulnerabilityCollection(EndpointCollection):
    @as_object(AsyncSearchResponse)
    def create_async_search(self, vulnerability_id: str):
        resource = "vulnerabilities/async_search"

        return self.call(
            self.methods.POST, resource, params={"vulnerability_id": vulnerability_id}
        )

    @as_object(Vulnerabilities, transform=Vulnerabilities)
    def get_async_search(self, async_search_id: str):
        resource = f"vulnerabilities/async_search/{async_search_id}"

        return self.call(self.methods.GET, resource)

    @as_object(AsyncSearchResponse)
    def search_vulnerability_solutions(self, vulnerability_id: str):
        resource = "vulnerability/solutions/async_search"

        return self.call(
            self.methods.POST, resource, params={"vulnerability_id": vulnerability_id}
        )

    @as_object(Solutions, transform=Solutions)
    def get_vulnerability_solutions(self, async_search_id: str):
        resource = f"vulnerability/solutions/async_search/{async_search_id}"

        return self.call(self.methods.GET, resource)
