from nldcsc.http_apis.viper.collections.bases import EndpointCollection
from nldcsc.http_apis.viper.collections.utils import requires_login


class GeneralCollection(EndpointCollection, prefix="general"):
    @requires_login
    def app_details(self):
        resource = "app_details"

        return self.call(self.methods.GET, resource)
