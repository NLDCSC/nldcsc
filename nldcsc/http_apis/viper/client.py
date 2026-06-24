from functools import cached_property


from nldcsc.http_apis.base_class.cached_base_class import CachedAPI
from nldcsc.http_apis.viper.collections.v1 import V1Collection


from .collections.auth.objects import AuthInfo
from .collections.unversioned import UnversionedCollection


class ViperClient(CachedAPI):
    def __init__(
        self,
        baseurl,
        auth: tuple[str, str] = tuple(),
        api_path=None,
        proxies=None,
        user_agent="ViperClient",
        verify=True,
        timeout=10,
        max_sessions=128,
        persist_self=True,
        default_retry=None,
        default_expiry=3600,
        default_backend=None,
        **requests_kwargs
    ):
        super().__init__(
            baseurl,
            api_path,
            proxies,
            user_agent,
            verify,
            timeout,
            max_sessions,
            persist_self,
            default_retry,
            default_expiry,
            default_backend,
            **requests_kwargs
        )

        self.auth_info = AuthInfo(*auth)

    def get_token(self): ...

    @cached_property
    def unversioned(self):
        return UnversionedCollection(client=self)

    @cached_property
    def v1(self):
        return V1Collection(client=self)
