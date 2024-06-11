import contextlib
import logging
from collections import namedtuple
from typing import Any

import httpx
from httpx import (
    Client,
    AsyncClient,
    HTTPTransport,
    AsyncHTTPTransport,
    HTTPError,
    Response,
)
from nldcsc.loggers.app_logger import AppLogger

logging.setLoggerClass(AppLogger)


class HttpxBaseClass(object):

    def __init__(
        self,
        baseurl: str,
        api_path: str = None,
        proxies: dict = None,
        user_agent: str = "HttpxBaseClass",
        use_async_client: bool = True,
        **kwargs,
    ):
        """
        The Generic api caller handles all communication towards an api resource.
        """
        self.logger = logging.getLogger(self.__class__.__name__)

        if "verify" not in kwargs:
            self.verify = False
        else:
            self.verify = kwargs.pop("verify")

        if "follow_redirects" not in kwargs:
            self.follow_redirects = True
        else:
            self.follow_redirects = kwargs.pop("follow_redirects")

        if "http2" not in kwargs:
            self.http2 = True
        else:
            self.http2 = kwargs.pop("http2")

        self.baseurl = baseurl
        self.api_path = api_path
        self.proxies = proxies
        self.user_agent = user_agent
        self.use_async_client = use_async_client
        self.kwargs = kwargs

        self.methods = namedtuple("methods", "GET POST DELETE PUT PATCH")(
            "GET", "POST", "DELETE", "PUT", "PATCH"
        )

        self.myheaders = self.__default_headers

    def __repr__(self) -> str:
        """return a string representation of the obj GenericApi"""
        return f"<< {self.__class__.__name__}:{self.baseurl} >>"

    def _build_url(self, resource: str) -> str:
        """
        Internal method to build an url to use when executing commands
        """
        if self.api_path is None:
            return f"{self.baseurl}/{resource}"
        else:
            return f"{self.baseurl}/{self.api_path}/{resource}"

    @property
    def __default_headers(self) -> dict:
        """
        Property to return the default headers
        """
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": f"{self.user_agent}",
        }

    @property
    def headers(self) -> dict:
        """
        Property to return the current headers
        """

        return self.myheaders

    def set_header_field(self, field: str, value: str) -> dict:
        """
        Method to add a header and set its value
        """
        try:
            self.myheaders[field] = value
            return self.myheaders
        except TypeError:
            self.myheaders = {field: value}
            return self.myheaders

    def del_header_field(self, field: str) -> dict:
        """
        Method to delete a header field
        """

        self.myheaders.pop(field)

        return self.myheaders

    def reset_headers(self):
        """
        Method to reset the headers to the default values
        """

        self.myheaders = self.__default_headers

    def clear_headers(self):
        """
        Method to clear the headers and the myheaders to None
        """
        self.myheaders = None

    def create_sync_client(self, **kwargs) -> Client:
        transport = HTTPTransport(retries=3, http2=self.http2)
        client = httpx.Client(
            verify=self.verify,
            proxies=self.proxies,
            follow_redirects=self.follow_redirects,
            transport=transport,
            http2=self.http2,
            **kwargs,
        )

        return client

    def create_async_client(self, **kwargs) -> AsyncClient:
        transport = AsyncHTTPTransport(retries=3, http2=self.http2)
        client = httpx.AsyncClient(
            verify=self.verify,
            proxies=self.proxies,
            follow_redirects=self.follow_redirects,
            transport=transport,
            http2=self.http2,
            **kwargs,
        )

        return client

    def get_client(self) -> Client | AsyncClient:
        if self.use_async_client:
            return self.create_async_client(**self.kwargs)
        else:
            return self.create_sync_client(**self.kwargs)

    @contextlib.contextmanager
    def get_cm_client(self) -> Client | AsyncClient:
        client = self.get_client()

        try:
            yield client
        except Exception as err:
            self.logger.warning(f"Error requesting client context manager: {err}")
            self.logger.exception(err)
        finally:
            client.close()

    def call(
        self,
        method: str = None,
        resources: str | list = None,
        data: dict = None,
        timeout: int = 60,
        stream: bool = False,
        generic_request: bool = False,
    ) -> Response | str | Any:
        """
        Method for requesting free format api resources
        """
        try:
            if stream:
                request_api_resource = {
                    "headers": self.myheaders,
                    "timeout": timeout,
                }

                with self.get_client() as client:
                    if isinstance(resources, str):
                        with client.stream(
                            method, resources, **request_api_resource
                        ) as response_stream:
                            # returning complete body; but other iter_* methods might be better suited for
                            # specific cases
                            return response_stream.read()
                    else:
                        raise TypeError(
                            "For streaming responses; resources must be a string"
                        )
            else:
                with self.get_client() as client:
                    if isinstance(resources, list):
                        results = []
                        for resource in resources:
                            results.append(
                                self._s_connect(
                                    method=method,
                                    resource=resource,
                                    client=client,
                                    data=data,
                                    timeout=timeout,
                                    generic_request=generic_request,
                                )
                            )
                    else:
                        resource = resources
                        results = self._s_connect(
                            method=method,
                            resource=resource,
                            client=client,
                            data=data,
                            timeout=timeout,
                            generic_request=generic_request,
                        )
                    return results
        except HTTPError:
            raise
        except Exception:
            raise

    async def a_call(
        self,
        method: str = None,
        resources: str | list = None,
        data: dict = None,
        timeout: int = 60,
        stream: bool = False,
        generic_request: bool = False,
    ) -> Response | str | Any:
        """
        Method for requesting free format api resources
        """
        try:
            if stream:
                request_api_resource = {
                    "headers": self.myheaders,
                    "timeout": timeout,
                }

                async with self.get_client() as client:
                    if isinstance(resources, str):
                        with client.stream(
                            method, resources, **request_api_resource
                        ) as response_stream:
                            # returning complete body; but other iter_* methods might be better suited for
                            # specific cases
                            return await response_stream.read()
                    else:
                        raise TypeError(
                            "For streaming responses; resources must be a string"
                        )
            else:
                async with self.get_client() as client:
                    if isinstance(resources, list):
                        results = []
                        for resource in resources:
                            results.append(
                                await self._a_connect(
                                    method=method,
                                    resource=resource,
                                    client=client,
                                    data=data,
                                    timeout=timeout,
                                    generic_request=generic_request,
                                )
                            )
                    else:
                        resource = resources
                        results = await self._a_connect(
                            method=method,
                            resource=resource,
                            client=client,
                            data=data,
                            timeout=timeout,
                            generic_request=generic_request,
                        )
                    return results
        except HTTPError:
            raise
        except Exception:
            raise

    def _s_connect(
        self,
        method: str,
        resource: str,
        client: Client,
        data: dict | bytes = None,
        timeout: int = 60,
        generic_request: bool = False,
    ) -> Response | str | Any:
        """
        Send a request
        """

        request_api_resource = {
            "headers": self.myheaders,
            "timeout": timeout,
        }

        if data is not None:
            if method in [self.methods.DELETE, self.methods.GET]:
                if not isinstance(data, bytes):
                    raise TypeError(
                        f"'data' body (data == dict) type for {method} is not supported; use content (data == bytes) "
                        f"instead. Or set generic_request to 'True'"
                    )
                request_api_resource["content"] = data
            else:
                request_api_resource["data"] = data

        try:
            if generic_request:
                r = client.request(
                    method, self._build_url(resource), **request_api_resource
                )
            else:
                r = getattr(client, method.lower())(
                    self._build_url(resource), **request_api_resource
                )

            return r
        except HTTPError:
            raise
        except Exception as err:
            raise Exception(err)

    async def _a_connect(
        self,
        method: str,
        resource: str,
        client: AsyncClient,
        data: dict | bytes = None,
        timeout: int = 60,
        generic_request: bool = False,
    ) -> Response | str | Any:
        """
        Send a request
        """
        request_api_resource = {
            "headers": self.myheaders,
            "timeout": timeout,
        }

        if data is not None:
            if method in [self.methods.DELETE, self.methods.GET]:
                if not isinstance(data, bytes):
                    raise TypeError(
                        f"'data' body (data == dict) type for {method} is not supported; use content (data == bytes) "
                        f"instead. Or set generic_request to 'True'"
                    )
                request_api_resource["content"] = data
            else:
                request_api_resource["data"] = data

        try:
            if generic_request:
                r = await client.request(
                    method, self._build_url(resource), **request_api_resource
                )
            else:
                r = await getattr(client, method.lower())(
                    self._build_url(resource), **request_api_resource
                )

            return r
        except HTTPError:
            raise
        except Exception as err:
            raise Exception(err)
