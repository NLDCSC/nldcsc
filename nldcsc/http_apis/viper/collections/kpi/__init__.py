from functools import partial

from nldcsc.http_apis.viper.collections.bases import (
    EndpointCollection,
)
from nldcsc.http_apis.viper.collections.kpi.objects import KPIType, KPIResponse
from nldcsc.http_apis.viper.collections.utils import as_object, signature_of
from nldcsc.http_apis.viper.objects import (
    AsyncSearchResponse,
    ExtendedListOperator,
    IntOperator,
)


class KPICollection(EndpointCollection, prefix="kpi"):
    @as_object(AsyncSearchResponse)
    def create_async_search(
        self,
        sort: str = "timestamp:desc",
        start_time: int | None = None,
        end_time: int | None = None,
        names: list[str] | None = None,
        kpi_types: list[KPIType] | None = None,
        teams: list[str] | None = None,
        start_time_operator: IntOperator | str = IntOperator.GE,
        end_time_operator: IntOperator | str = IntOperator.LE,
        names_operator: ExtendedListOperator | str = ExtendedListOperator.IN,
        kpi_types_operator: ExtendedListOperator | str = ExtendedListOperator.IN,
        teams_operator: ExtendedListOperator | str = ExtendedListOperator.IN,
    ):
        resource = "async_search"

        data = {"sort": sort}

        if start_time is not None:
            data["start_time"] = start_time
            data["start_time_operator"] = start_time_operator

        if end_time is not None:
            data["end_time"] = end_time
            data["end_time_operator"] = end_time_operator

        if names:
            data["name"] = names
            data["name_operator"] = names_operator

        if kpi_types:
            data["kpi_type"] = kpi_types
            data["kpi_type_operator"] = kpi_types_operator

        if teams:
            data["team"] = teams
            data["team_operator"] = teams_operator

        return self.call(self.methods.POST, resource, params=data)

    @as_object(KPIResponse)
    def get_async_search(
        self,
        async_search_id: str,
        page: int = 0,
        size: int = 50,
        sort: str = "timestamp:desc",
        start_time: int | None = None,
        end_time: int | None = None,
        names: list[str] | None = None,
        kpi_types: list[KPIType] | None = None,
        teams: list[str] | None = None,
        start_time_operator: IntOperator | str = IntOperator.GE,
        end_time_operator: IntOperator | str = IntOperator.LE,
        names_operator: ExtendedListOperator | str = ExtendedListOperator.IN,
        kpi_types_operator: ExtendedListOperator | str = ExtendedListOperator.IN,
        teams_operator: ExtendedListOperator | str = ExtendedListOperator.IN,
    ):
        resource = f"async_search/{async_search_id}"

        data = {"sort": sort, "page": page, "size": size}

        if start_time is not None:
            data["start_time"] = start_time
            data["start_time_operator"] = start_time_operator

        if end_time is not None:
            data["end_time"] = end_time
            data["end_time_operator"] = end_time_operator

        if names:
            data["name"] = names
            data["name_operator"] = names_operator

        if kpi_types:
            data["kpi_type"] = kpi_types
            data["kpi_type_operator"] = kpi_types_operator

        if teams:
            data["team"] = teams
            data["team_operator"] = teams_operator

        return self.call(self.methods.GET, resource, params=data)

    @signature_of(get_async_search)
    def iter_async_search(
        self, async_search_id: str, page: int = 0, size: int = 50, *args, **kwargs
    ):
        yield from self.iter_endpoint(
            partial(self.get_async_search, async_search_id), page, size, *args, **kwargs
        )
