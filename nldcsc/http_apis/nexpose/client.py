from functools import wraps
from typing import Callable, Literal, Type, TypeVar, Union

from nldcsc.http_apis.base_class.cached_base_class import CachedAPI
from .objects import NexposeAssets

T = TypeVar("T")


def as_object(
    obj: Type[T], transform: Callable[..., T] = None
) -> Callable[..., Callable[..., T]]:
    def wrapper(f) -> Callable[..., T]:
        @wraps
        def inner(*args, **kwargs) -> T:
            r = f(*args, **kwargs)

            if transform:
                return transform(r)
            return obj(**r)

        return inner

    return wrapper


class NexposeClient(CachedAPI):
    @as_object(NexposeAssets, NexposeAssets.from_dict)
    def get_assets(
        self,
        page: int = 0,
        size: int = 10,
        sorting: list[tuple[str, Union[Literal["ASC"], Literal["DESC"]]]] = None,
    ):
        resource = "assets"

        params = {
            "page": page,
            "size": size,
        }

        if sorting:
            params["sort"] = [f"{field},{order}" for field, order in sorting]

        return self.call(self.methods.GET, resource, params=params)

    def iter_assets(
        self,
        offset: int = 0,
        batch_size: int = 100,
        sorting: list[tuple[str, Union[Literal["ASC"], Literal["DESC"]]]] = None,
    ):
        page = batch_size // offset

        while True:
            assets = self.get_assets(page, batch_size, sorting)

            page += 1

            if assets.page.number == assets.page.total_pages:
                ...

            if page * batch_size < offset:
                pass
