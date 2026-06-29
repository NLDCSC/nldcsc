from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Generator, Type, TypeVar

from dataclasses_json import DataClassJsonMixin

if TYPE_CHECKING:
    from nldcsc.http_apis.viper.client import ViperClient

T = TypeVar("T")


@dataclass
class PaginatedResponse(DataClassJsonMixin):
    total: int
    page: int
    size: int
    pages: int
    items: list[Any]

    @property
    def has_next_page(self):
        return self.page < self.pages


P = TypeVar("P", bound=PaginatedResponse)


class EndpointCollection:
    _prefix: str | None = None

    def __init_subclass__(cls, prefix: str | None = None, **kwargs):
        super().__init_subclass__(**kwargs)

        if prefix:
            cls._prefix = prefix.strip("/")

    def __init__(self, client: ViperClient, prefix: str | None = None):
        self.client = client
        self.prefix = self._build_prefix_path(prefix)

    def get_collection(self, collection: Type[T]) -> T:
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

    def iter_endpoint(
        self, function: Callable[[int, int], P], page: int, size: int, *args, **kwargs
    ) -> Generator[P, None, None]:
        r = function(page, size, *args, **kwargs)

        yield from r.items

        while r.has_next_page:
            page += 1

            r = function(page, size, *args, **kwargs)

            yield from r.items

    def call(self, method: str, resource: str = None, **kwargs):
        return self.client.call(method, self._build_resource_path(resource), **kwargs)
