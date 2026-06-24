from nldcsc.http_apis.viper.collections.bases import EndpointCollection
from nldcsc.http_apis.viper.collections.utils import as_object

from .objects import AuthResponse


class AuthCollection(EndpointCollection, prefix="auth"):
    @as_object(AuthResponse)
    def login(
        self,
        username: str,
        password: str,
    ):
        resource = "login"

        return self.call(
            self.methods.POST,
            resource,
            data={"username": username, "password": password},
        )
