from nldcsc.http_apis.viper.collections.bases import EndpointCollection
from nldcsc.http_apis.viper.collections.utils import as_object

from .objects import MeResponse, AsyncSearchesResponse, AsyncSearchState


class UserCollection(EndpointCollection, prefix="user"):
    @as_object(MeResponse)
    def me(self):
        resource = "me"

        return self.call(self.methods.GET, resource)

    @as_object(AsyncSearchesResponse)
    def async_searches(
        self,
        page: int = 0,
        size: int = 50,
        sort: str = "created:desc",
        state: AsyncSearchState | str = AsyncSearchState.ALL,
    ):
        resource = "async_searches"

        return self.call(
            self.methods.GET,
            resource,
            params={"page": page, "size": size, "sort": sort, "state": state},
        )
