from nldcsc.http_apis.base_class.api_base_class import ApiBaseClass


class ProvidentiaApi(ApiBaseClass):
    def __init__(
        self,
        baseurl: str,
        api_path: str = "v3",
        proxies: dict = None,
        user_agent: str = "NLDCSC",
        api_key: str = "",
        **kwargs,
    ):
        super().__init__(
            baseurl=baseurl,
            api_path=api_path,
            proxies=proxies,
            user_agent=user_agent,
            **kwargs,
        )

        self.set_header_field("Authorization", f"Bearer {api_key}")

    def environments(self) -> dict[str, list[dict[str, str]]]:
        resource = ""
        return self.call(self.methods.GET, resource)

    def environment(self, environment: str) -> dict:
        resource = f"/{environment}"
        return self.call(self.methods.GET, resource)

    def environment_hosts(self, environment: str) -> dict:
        resource = f"/{environment}/hosts"
        return self.call(self.methods.GET, resource)

    def environment_hosts_id(self, environment: str, host_id: str) -> dict:
        resource = f"/{environment}/hosts/{host_id}"
        return self.call(self.methods.GET, resource)

    def environment_inventory(self, environment: str) -> dict:
        resource = f"/{environment}/inventory"
        return self.call(self.methods.GET, resource)

    def environment_networks(self, environment: str) -> dict:
        resource = f"/{environment}/networks"
        return self.call(self.methods.GET, resource)

    def environment_tags(self, environment: str) -> dict:
        resource = f"/{environment}/tags"
        return self.call(self.methods.GET, resource)

    def environment_actors(self, environment: str) -> dict:
        resource = f"/{environment}/actors"
        return self.call(self.methods.GET, resource)

    def environment_services(self, environment: str) -> dict:
        resource = f"/{environment}/services"
        return self.call(self.methods.GET, resource)

    def environment_services_id(self, environment: str, service_id: str) -> dict:
        resource = f"/{environment}/services/{service_id}"
        return self.call(self.methods.GET, resource)
