from nldcsc.http_apis.viper.collections.admin import AdminCollection
from nldcsc.http_apis.viper.collections.async_searches import AsyncSearchCollection
from nldcsc.http_apis.viper.collections.auth import AuthCollection
from nldcsc.http_apis.viper.collections.bases import EndpointCollection
from nldcsc.http_apis.viper.collections.general import GeneralCollection
from nldcsc.http_apis.viper.collections.kpi import KPICollection
from nldcsc.http_apis.viper.collections.user import UserCollection
from nldcsc.http_apis.viper.collections.oracledb import OracleDBCollection


class V1Collection(EndpointCollection, prefix="v1"):
    @property
    def general(self):
        return self.get_collection(GeneralCollection)

    @property
    def auth(self):
        return self.get_collection(AuthCollection)

    @property
    def user(self):
        return self.get_collection(UserCollection)

    @property
    def admin(self):
        return self.get_collection(AdminCollection)

    @property
    def async_search(self):
        return self.get_collection(AsyncSearchCollection)

    @property
    def kpi(self):
        return self.get_collection(KPICollection)

    @property
    def oracle_db(self):
        return self.get_collection(OracleDBCollection)
