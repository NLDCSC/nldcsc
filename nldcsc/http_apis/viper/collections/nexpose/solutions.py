from nldcsc.http_apis.viper.collections.bases import EndpointCollection
from nldcsc.http_apis.viper.collections.utils import as_object
from nldcsc.http_apis.viper.objects import AsyncSearchResponse

from .objects import Solutions


class SolutionDocument(EndpointCollection, prefix="solution"):
    @as_object(AsyncSearchResponse)
    def create_async_search(self, solution_id: str):
        resource = "async_search"

        return self.call(
            self.methods.POST, resource, params={"solution_id": solution_id}
        )

    @as_object(Solutions, transform=Solutions)
    def get_async_search(self, async_search_id: str):
        resource = f"async_search/{async_search_id}"

        return self.call(self.methods.GET, resource)


class SolutionCollection(EndpointCollection, prefix="solutions"):
    @as_object(AsyncSearchResponse)
    def create_async_search(self):
        return self.call(self.methods.POST, "async_search")

    @as_object(Solutions, transform=Solutions)
    def get_async_search(self, async_search_id: str):
        return self.call(self.methods.GET, f"async_search/{async_search_id}")
