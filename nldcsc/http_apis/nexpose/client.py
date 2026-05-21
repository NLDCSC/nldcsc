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
    """
    Wrapper to transform a dict into a object.

    Args:
        obj (Type[T]): Object to to transform to.
        transform (Callable[..., T], optional): Method that transforms the dict into the object. Defaults to None.

    Returns:
        Callable[..., Callable[..., T]]: Wrapper that transforms the dict into the object.
    """

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
        """
        Transforms page, size and sorting (pss) to a params dict.

        Args:
            page (int, optional): page to start 0 indexed. Defaults to 0.
            size (int, optional): size per page. Defaults to 10.
            sorting (Sorting, optional): how to sort the page. Defaults to None.

        Returns:
            dict: params formatted as dict
        """

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
        """
        Reusable generator to iter through paginated nexpose responses.

        Args:
            source (NexposePageSource[T]): Function to call and get a paginated response; function should accept kwarg 'page'
            offset (int, optional): Amount of resources to initially skip. Defaults to 0.
            batch_size (int, optional): Amount of resources to retrieve per page. Defaults to 100.

        Yields:
            T: Type that is returned from the source function as resource
        """
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
        """
        gets an page of assets.

        Args:
            page (int, optional): page number to retrieve. Defaults to 0.
            size (int, optional): amount of resources on the page. Defaults to 10.
            sorting (Sorting, optional): how to sort the assets. Defaults to None.
            filters (list[NexposeFilter], optional): filters to apply to search for specific assets. Defaults to None.
            match ( NexposeSearchMatch, optional): match method to use when searching. Defaults to NexposeSearchMatch.ALL.

        Returns:
            NexposeAssets: paginated response
        """
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
        """
        iter asset from pages starting at an offset.

        Args:
            offset (int, optional): offset to start iterating from. Defaults to 0.
            batch_size (int, optional): amount of assets to retrieve per page. Defaults to 100.
            sorting (Sorting, optional): how the assets are sorted. Defaults to None.
            filters (list[NexposeFilter], optional): filters to apply to the assets. Defaults to None.
            match ( NexposeSearchMatch, optional): match method to use when searching. Defaults to NexposeSearchMatch.ALL..

        Yields:
            NexposeResource: Singular asset
        """
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
        """
        iter asset vulnerabilities starting at an offset.

        Args:
            asset_id (int): asset id to retrieve vulnerabilities from.
            offset (int, optional): offset to start iterating from. Defaults to 0.
            batch_size (int, optional): amount of assets to retrieve per page. Defaults to 100.
            sorting (Sorting, optional): how the assets are sorted. Defaults to None.

        Yields:
            NexposeVulnerability: Singular vulnerability on the requested asset
        """

    @as_object(NexposeAssetVulnerabilities, NexposeAssetVulnerabilities.from_dict)
    def get_asset_vulnerabilities(
        self, asset_id: int, page: int = 0, size: int = 10, sorting: Sorting = None
    ):
        """
        Get asset vulnerabilities.

        Args:
            asset_id (int): asset id to retrieve vulnerabilities from.
            page (int, optional): page to retrieve. Defaults to 0.
            size (int, optional): page size. Defaults to 10.
            sorting (Sorting, optional): how to sort the assets. Defaults to None.

        Returns:
            NexposeAssetVulnerabilities: paginated response
        """
        resource = f"assets/{asset_id}/vulnerabilities"

        return self.call(
            self.methods.GET, resource, params=self._pss_to_params(page, size, sorting)
        )

    @as_object(NexposeResource, NexposeResource.from_dict)
    def get_asset(self, asset_id: int):
        """
        Get a singular asset by id.

        Args:
            asset_id (int): asset id of asset to retrieve.

        Returns:
            NexposeResource: singular asset
        """
        resource = f"assets/{asset_id}"

        return self.call(self.methods.GET, resource)

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.build_url(None)})>"
