from nldcsc.http_apis.viper.collections.bases import EndpointCollection
from .assets import AssetCollection
from .vulnerabilities import VulnerabilityCollection
from .solutions import SolutionCollection


class NexposeCollection(EndpointCollection, prefix="nexpose"):

    @property
    def assets(self):
        return self.get_collection(AssetCollection)

    @property
    def vulnerabilities(self):
        return self.get_collection(VulnerabilityCollection)

    @property
    def solutions(self):
        return self.get_collection(SolutionCollection)
