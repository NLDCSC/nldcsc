from functools import wraps
from typing import Literal, Union

from nldcsc.http_apis.base_class.cached_base_class import CachedAPI
from .objects import NexposeAssets


def as_object(obj):
    def wrapper(f):
        @wraps
        def inner(*args, **kwargs):
            r = f(*args, **kwargs)

            return obj(r)

        return inner

    return wrapper


class NexposeClient(CachedAPI):
    @as_object(NexposeAssets)
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
