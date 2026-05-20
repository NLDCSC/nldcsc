from functools import partial, wraps
from typing import Callable, Literal, Protocol, Type, TypeAlias, TypeVar, Union

from nldcsc.http_apis.base_class.cached_base_class import CachedAPI
from .objects import (
    NexposeAssetVulnerabilities,
    NexposeAssets,
    NexposeLink,
    NexposePage,
    NexposeResource,
    NexposeSortingDirection,
    NexposeSearchMatch,
    NexposeFilter,
)

T = TypeVar("T")


def as_object(
    obj: Type[T], transform: Callable[..., T] = None
) -> Callable[..., Callable[..., T]]:
    def wrapper(f) -> Callable[..., T]:
        @wraps(f)
        def inner(*args, **kwargs) -> T:
            r = f(*args, **kwargs)

            try:
                if transform:
                    return transform(r)
                return obj(**r)
            except Exception as e:
                raise ValueError(
                    f"Failed transforming response for {f.__name__} into {obj=} -> {e=}"
                )

        return inner

    return wrapper


Sorting: TypeAlias = list[
    tuple[str, Union[Literal["ASC"], Literal["DESC"], NexposeSortingDirection]]
]


class NexposePageResponse(Protocol[T]):
    links: list[NexposeLink]
    page: NexposePage
    resources: list[T]


class NexposePageSource(Protocol[T]):
    def __call__(self, page: int) -> NexposePageResponse[T]: ...


class NexposeClient(CachedAPI):
    def _pss_to_params(self, page: int = 0, size: int = 10, sorting: Sorting = None):

        params = {
            "page": page,
            "size": size,
        }

        if sorting:
            params["sort"] = [f"{field},{order}" for field, order in sorting]

        return params

    def _iter_pages(
        self,
        source: NexposePageSource[T],
        offset: int = 0,
        batch_size: int = 100,
    ):
        page = offset // batch_size
        skip = offset % batch_size

        while True:
            assets = source(page=page)

            page += 1

            if skip:
                assets.resources = assets.resources[skip:]
                skip = 0

            yield from assets.resources

            if assets.page is None or page >= assets.page.total_pages:
                break

    @as_object(NexposeAssets, NexposeAssets.from_dict)
    def get_assets(
        self,
        page: int = 0,
        size: int = 10,
        sorting: Sorting = None,
        filters: list[NexposeFilter] = None,
        match: Union[
            Literal["any"], Literal["all"], NexposeSearchMatch
        ] = NexposeSearchMatch.ALL,
    ):
        params = self._pss_to_params(page, size, sorting)

        if filters:
            resource = "assets/search"

            return self.call(
                self.methods.POST,
                resource,
                params=params,
                json={"filters": filters, "match": match},
            )

        else:
            resource = "assets"

            return self.call(self.methods.GET, resource, params=params)

    def iter_assets(
        self,
        offset: int = 0,
        batch_size: int = 100,
        sorting: Sorting = None,
        filters: list[NexposeFilter] = None,
        match: Union[
            Literal["any"], Literal["all"], NexposeSearchMatch
        ] = NexposeSearchMatch.ALL,
    ):
        yield from self._iter_pages(
            partial(
                self.get_assets,
                size=batch_size,
                sorting=sorting,
                filters=filters,
                match=match,
            ),
            offset,
            batch_size,
        )

    def iter_asset_vulnerabilities(
        self,
        asset_id: int,
        offset: int = 0,
        batch_size: int = 100,
        sorting: Sorting = None,
    ):
        yield from self._iter_pages(
            partial(
                self.get_asset_vulnerabilities,
                asset_id=asset_id,
                size=batch_size,
                sorting=sorting,
            ),
            offset,
            batch_size,
        )

    @as_object(NexposeAssetVulnerabilities, NexposeAssetVulnerabilities.from_dict)
    def get_asset_vulnerabilities(
        self, asset_id: int, page: int = 0, size: int = 10, sorting: Sorting = None
    ):
        resource = f"assets/{asset_id}/vulnerabilities"

        return self.call(
            self.methods.GET, resource, params=self._pss_to_params(page, size, sorting)
        )

    @as_object(NexposeResource, NexposeResource.from_dict)
    def get_asset(self, asset_id: int):
        resource = f"assets/{asset_id}"

        return self.call(self.methods.GET, resource)
