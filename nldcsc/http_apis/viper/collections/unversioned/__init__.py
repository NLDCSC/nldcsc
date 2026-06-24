from nldcsc.http_apis.viper.collections.bases import EndpointCollection
from nldcsc.http_apis.viper.collections.unversioned.objects import (
    WelcomeResponse,
    ChangelogResponse,
)
from nldcsc.http_apis.viper.collections.utils import as_object


class UnversionedCollection(EndpointCollection):
    @as_object(WelcomeResponse)
    def welcome(self):
        resource = ""

        return self.call(self.methods.GET, resource)

    @as_object(ChangelogResponse)
    def changelog(self):
        resource = "changelog"

        return self.call(self.methods.GET, resource)
