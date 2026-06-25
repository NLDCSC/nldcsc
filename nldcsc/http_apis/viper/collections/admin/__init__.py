from nldcsc.http_apis.viper.collections.bases import EndpointCollection
from nldcsc.http_apis.viper.collections.utils import as_object

from .objects import StatusResponse


class AdminCollection(EndpointCollection, prefix="admin"):
    @as_object(StatusResponse)
    def status(
        self,
    ):
        resource = "status"

        return self.call(
            self.methods.GET,
            resource,
        )
