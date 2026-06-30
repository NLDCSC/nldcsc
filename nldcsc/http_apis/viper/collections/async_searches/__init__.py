from nldcsc.http_apis.viper.collections.bases import EndpointCollection
from nldcsc.http_apis.viper.collections.utils import as_object
from nldcsc.http_apis.viper.objects import AsyncSearchResponse


class AsyncSearchCollection(EndpointCollection, prefix="async_search"):
    @as_object(AsyncSearchResponse)
    def get(self, async_search_id: str):
        resource = async_search_id

        return self.call(
            self.methods.GET,
            resource,
        )
