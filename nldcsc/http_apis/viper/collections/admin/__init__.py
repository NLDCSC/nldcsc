from typing import Any, Callable, Concatenate, ParamSpec, TypeVar

from nldcsc.http_apis.viper.collections.bases import EndpointCollection
from nldcsc.http_apis.viper.collections.utils import as_object, signature_of
from nldcsc.http_apis.viper.objects import (
    AsyncSearchState,
    AsyncSearchesResponse,
    IntOperator,
    ListOperator,
)

from .objects import AuditLogResponse, StatusResponse, UserAction


class AdminCollection(EndpointCollection, prefix="admin"):
    @as_object(StatusResponse)
    def status(
        self,
    ):
        resource = "status"

        return self.call(
            self.methods.GET,
            resource,
        )

    @as_object(AsyncSearchesResponse)
    def async_searches(
        self,
        page: int = 0,
        size: int = 50,
        sort: str = "created:desc",
        state: AsyncSearchState | str = AsyncSearchState.ALL,
    ):
        resource = "async_searches"

        return self.call(
            self.methods.GET,
            resource,
            params={"page": page, "size": size, "sort": sort, "state": state},
        )

    @as_object(AuditLogResponse)
    def audit_log(
        self,
        page: int = 0,
        size: int = 50,
        sort: str = "timestamp:desc",
        start_time: int = 0,
        end_time: int | None = None,
        usernames: list[str] | None = None,
        user_actions: list[UserAction] | None = None,
        request_ids: list[str] | None = None,
        start_time_operator: IntOperator | str = IntOperator.GE,
        end_time_operator: IntOperator | str = IntOperator.LE,
        username_operator: ListOperator | str = ListOperator.IN,
        user_action_operator: ListOperator | str = ListOperator.IN,
        request_id_operator: ListOperator | str = ListOperator.IN,
    ):
        resource = "audit_log"

        data = {
            "page": page,
            "size": size,
            "sort": sort,
            "start_time": start_time,
            "start_time_operator": start_time_operator,
            "end_time_operator": end_time_operator,
        }

        if end_time:
            data["end_time"] = end_time

        if usernames:
            data["username"] = usernames
            data["username_operator"] = username_operator

        if user_actions:
            data["user_action"] = user_actions
            data["user_action_operator"] = user_action_operator

        if request_ids:
            data["request_id"] = request_ids
            data["request_id_operator"] = request_id_operator

        return self.call(self.methods.GET, resource, params=data)

    @signature_of(audit_log)
    def iter_audit_log(self, page: int = 0, size: int = 50, *args, **kwargs):
        yield from self.iter_endpoint(self.audit_log, page, size, *args, **kwargs)

    @signature_of(async_searches)
    def iter_async_searches(self, page: int = 0, size: int = 50, *args, **kwargs):
        yield from self.iter_endpoint(self.async_searches, page, size, *args, **kwargs)
