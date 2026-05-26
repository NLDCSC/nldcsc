from nldcsc.http_apis.base_class.cached_base_class import CachedAPI


class ConfluenceClient(CachedAPI):
    def __init__(
        self,
        baseurl,
        api_path="rest/api",
        token: str = None,
        proxies=None,
        user_agent="CachedApi",
        verify=True,
        timeout=10,
        max_sessions=128,
        persist_self=True,
        default_retry=None,
        default_expiry=3600,
        default_backend=None,
        **requests_kwargs,
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
            **requests_kwargs,
        )

        if token:
            self.set_header("Authorization", f"Bearer {token}")

    def search(self, cql: str):
        resource = "search"

        return self.call(self.methods.GET, resource, params={"cql": cql})
