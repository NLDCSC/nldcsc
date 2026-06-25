from nldcsc.http_apis.viper.collections.bases import EndpointCollection
from nldcsc.http_apis.viper.collections.utils import as_object

from .objects import AppDetailsResponse, EndpointDetailsResponse


class GeneralCollection(EndpointCollection, prefix="general"):
    @as_object(AppDetailsResponse)
    def app_details(self):
        resource = "app_details"

        return self.call(self.methods.GET, resource)

    @as_object(EndpointDetailsResponse)
    def endpoint_details(self):
        resource = "endpoint_details"

        return self.call(self.methods.GET, resource)
