from typing import Type, TypeVar

from dataclasses_json import DataClassJsonMixin

from nldcsc.http_apis.base_class.api_base_class import ApiBaseClass

from .objects import (
    NCSCFeedIndex,
    NCSCFeedInfo,
    NCSCFeedItems,
    NCSCFeedUpdateSequenceList,
)

P = TypeVar("P", bound=DataClassJsonMixin)


class FBFClient(ApiBaseClass):
    def __init__(
        self,
        baseurl: str,
        auth: str,
        api_path: str = None,
        proxies=None,
        user_agent="nldcsc",
        **kwargs,
    ):
        super().__init__(baseurl, api_path, proxies, user_agent, **kwargs)

        self.set_header_field("access-token", auth)

    def call(
        self,
        method=None,
        resource=None,
        data=None,
        timeout=60,
        return_response_object=False,
        stream=False,
        ignore_api_path=False,
        files=None,
        response_dataclass: Type[P] = None,
    ):
        data = super().call(
            method,
            resource,
            data,
            timeout,
            return_response_object,
            stream,
            ignore_api_path,
            files,
        )

        if response_dataclass:
            return response_dataclass.from_dict(data)

        return data

    def get_info(self):
        return self.call(self.methods.GET)

    def get_ncsc_feeds(self):
        resource = "ncsc/feeds"

        self.call(self.methods.GET, resource=resource, response_dataclass=NCSCFeedInfo)

    def get_ncsc_feed_updates(self):
        resource = "ncsc/feeds/updates"

        self.call(
            self.methods.GET,
            resource=resource,
            response_dataclass=NCSCFeedUpdateSequenceList,
        )

    def get_ncsc_feed_index(
        self,
        feed: str,
        client: str,
        start: int = None,
        stop: int = None,
        inclusive: bool = True,
    ):
        """
        Create a index from a ncsc feed

        Args:
            feed (str): name of feed
            client (str): client identifier
            start (int, optional): start timestamp of the first item. Defaults to None.
            stop (int, optional): timestamp of the last item. Defaults to None.
            inclusive (bool, optional): include the start time. Defaults to True.
        """
        resource = f"ncsc/feeds/request/{feed}/{client}"

        params = {}

        if start is not None:
            params["start_time"] = start

        if stop is not None:
            params["stop_time"] = stop

        if inclusive is not None:
            params["include_start_time"] = inclusive

        return self.call(
            self.methods.GET,
            resource=resource,
            data=params,
            response_dataclass=NCSCFeedIndex,
        )

    def get_ncsc_feed_index_items(self, index: str, limit: int = 1000, offset: int = 0):
        """
        Get items from a ncsc feed index

        Args:
            index (str): name of index
            limit (int, optional): amount of items. Defaults to 1000.
            offset (int, optional): item offset. Defaults to 0.
        """
        resource = f"ncsc/feeds//process/{index}"

        params = {"limit": limit, "offset": offset}

        return self.call(
            self.methods.GET,
            resource=resource,
            data=params,
            response_dataclass=NCSCFeedItems,
        )

    def iter_ncsc_feed_index_items(
        self, index: str, batch_size: int = 1000, offset: int = 0
    ):
        """
        iter through a ncsc index

        Args:
            index (str): name of index
            batch_size (int, optional): size to request per request. Defaults to 1000.
            offset (int, optional): starting offset. Defaults to 0.
        """
        batch = 0

        while True:
            batch = self.get_ncsc_feed_index_items(
                index, batch_size, offset + batch_size * batch
            )

            yield from batch.entries

            if batch.last:
                break
