from collections.abc import Mapping, Sequence
from uuid import UUID

from nldcsc.http_apis.viper.collections.bases import EndpointCollection
from nldcsc.http_apis.viper.objects import BatchSearchResponse, BatchSearchQuery


MAX_BATCH_SEARCH_SIZE = 20


class InvalidBatchResponse(ValueError):
    """Viper's batch reply does not match the searches sent. Trust none of it."""


def _payload(search: BatchSearchQuery | Mapping) -> dict:
    if isinstance(search, BatchSearchQuery):
        return {
            key: value for key, value in search.to_dict().items() if value is not None
        }
    return dict(search)


def _validated(sent: list[dict], data: object) -> BatchSearchResponse:
    """check every outcome before any caller may act on a search ID."""
    items = data.get("searches") if isinstance(data, dict) else None
    if not isinstance(items, list) or len(items) != len(sent):
        raise InvalidBatchResponse("Viper must return one outcome per search.")
    ids = set()
    outcomes = []
    for query, item in zip(sent, items):
        if not isinstance(item, dict) or item.get("connector_id") != query.get(
            "connector_id"
        ):
            raise InvalidBatchResponse("Outcomes must follow order of the searches.")
        status = item.get("status_code")
        if type(status) is not int or not (status == 201 or 400 <= status <= 599):
            raise InvalidBatchResponse("Invalid outcome status.")
        search = item.get("search")
        if status != 201:
            if search is not None:
                raise InvalidBatchResponse("A failed outcome cannot carry a search.")
            outcomes.append(item)
            continue
        if not isinstance(search, dict) or item.get("error") is not None:
            raise InvalidBatchResponse("A started outcome needs a search and no error.")
        try:
            search_id = str(UUID(search["id"]))
        except (KeyError, TypeError, AttributeError, ValueError):
            raise InvalidBatchResponse("Search ID is invalid.") from None
        created = search.get("created")
        if search_id in ids or type(created) is not int or created < 0:
            raise InvalidBatchResponse("Duplicate search ID or invalid creation time.")
        ids.add(search_id)
        outcomes.append({**item, "search": {**search, "id": search_id}})
    return BatchSearchResponse.from_dict({"searches": outcomes})


class ConnectorsCollection(EndpointCollection, prefix="connectors"):
    def batch_search(
        self, searches: Sequence[BatchSearchQuery | Mapping]
    ) -> BatchSearchResponse:
        """Start 1 to 20 source searches in one request.

        the request is never sent twice: if Viper rejects the login token, the
        token is renewed and ViperTokenRenewed is raised instead of a retry,
        because a retry could start every search twice.
        """
        sent = [_payload(search) for search in searches]
        if not 1 <= len(sent) <= MAX_BATCH_SEARCH_SIZE:
            raise ValueError(f"Send 1 to {MAX_BATCH_SEARCH_SIZE} searches.")
        data = self.call(
            self.methods.POST,
            "batch_search",
            json={"searches": sent},
            replay_on_token_failure=False,
        )
        return _validated(sent, data)
