from functools import lru_cache
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from nldcsc.http_apis.viper.client import ViperClient


class EndpointCollection:
    _prefix: str | None = None

    def __init_subclass__(cls, prefix: str | None = None, **kwargs):
        super().__init_subclass__(**kwargs)

        if prefix:
            cls._prefix = prefix.strip("/")

    def __init__(self, client: ViperClient, prefix: str | None = None):
        self.client = client
        self.prefix = self._build_prefix_path(prefix)

    @lru_cache
    def get_collection(self, collection: "Type[EndpointCollection]"):
        return collection(self.client, self.prefix)

    def _build_prefix_path(self, prefix: str | None):
        path = []

        if prefix:
            path.append(prefix.strip("/"))

        if self._prefix:
            path.append(self._prefix)

        return "/".join(path)

    def _build_resource_path(self, resource: str):
        path = []

        if self.prefix:
            path.append(self.prefix)

        if resource:
            path.append(resource.lstrip("/"))

        return "/".join(path)

    @property
    def methods(self):
        return self.client.methods

    def call(self, method: str, resource: str = None, **kwargs):
        return self.client.call(method, self._build_resource_path(resource), **kwargs)
