from nldcsc.http_apis.viper.collections.bases import EndpointCollection
from nldcsc.http_apis.viper.collections.utils import as_object

from .objects import AuthResponse, LogoutResponse


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
            auth=None,
        )

    @as_object(AuthResponse)
    def refresh_token(self, refresh_token: str):
        resource = "refresh_token"

        return self.call(
            self.methods.POST, resource, data={"refresh_token": refresh_token}
        )

    @as_object(LogoutResponse)
    def logout(self, refresh_token: str):
        resource = "logout"

        return self.call(
            self.methods.POST, resource, data={"refresh_token": refresh_token}
        )
