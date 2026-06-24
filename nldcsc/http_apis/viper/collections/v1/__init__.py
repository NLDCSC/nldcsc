from nldcsc.http_apis.viper.collections.auth import AuthCollection
from nldcsc.http_apis.viper.collections.bases import EndpointCollection
from nldcsc.http_apis.viper.collections.general import GeneralCollection


class V1Collection(EndpointCollection, prefix="v1"):
    @property
    def general(self):
        return self.get_collection(GeneralCollection)

    @property
    def auth(self):
        return self.get_collection(AuthCollection)
