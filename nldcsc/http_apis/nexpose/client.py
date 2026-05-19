from functools import wraps
from typing import Callable, Literal, Type, TypeVar, Union

from nldcsc.http_apis.base_class.cached_base_class import CachedAPI
from .objects import NexposeAssets

T = TypeVar("T")


def as_object(
    obj: Type[T], transform: Callable[..., T] = None
) -> Callable[..., Callable[..., T]]:
    def wrapper(f) -> Callable[..., T]:
        @wraps(f)
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
        page = offset // batch_size
        skip = offset % batch_size

        assets = self.get_assets(page, batch_size, sorting)

        while assets.page.number < assets.page.total_pages:
            page += 1

            if skip:
                assets.resources = assets.resources[skip:]
                skip = 0

            yield from assets.resources
