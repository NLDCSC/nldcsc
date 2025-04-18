import json
from collections import namedtuple
import io
from json import JSONDecodeError
from typing import Any

import requests
from requests import Response
from requests.adapters import HTTPAdapter, Retry


class ApiBaseClass(object):
    """
    The GenericApi class serves as a base class for all API's
    """

    def __init__(
        self,
        baseurl: str,
        api_path: str = None,
        proxies: dict = None,
        user_agent: str = "ApiBaseClass",
        **kwargs,
    ):
        """
        The Generic api caller handles all communication towards an api resource.
        """

        if "verify" not in kwargs:
            self.verify = False
        else:
            self.verify = kwargs.pop("verify")

        self.baseurl = baseurl
        self.api_path = api_path
        self.proxies = proxies
        self.user_agent = user_agent
        self.kwargs = kwargs

        self.methods = namedtuple("methods", "GET POST DELETE PUT PATCH")(
            "GET", "POST", "DELETE", "PUT", "PATCH"
        )

        self.myheaders = self.__default_headers

    def __repr__(self) -> str:
        """return a string representation of the obj GenericApi"""
        return f"<<{self.__class__.__name__}: {self.baseurl}>>"

    def _build_url(self, resource: str, ignore_api_path: bool = False) -> str:
        """
        Internal method to build a url to use when executing commands
        """
        if self.api_path is None or ignore_api_path:
            return f"{self.baseurl}/{resource}"
        else:
            return f"{self.baseurl}/{self.api_path}/{resource}"

    def _connect(
        self,
        method: str,
        resource: str,
        session: requests.Session,
        data: dict | list | str | bytes | io.TextIOBase = None,
        timeout: int = 60,
        return_response_object: bool = False,
        stream: bool = False,
        ignore_api_path: bool = False,
    ) -> Response | str | Any:
        """
        Send a request

        Send a request to api host based on the specified data. Specify the content type as JSON and
        convert the data to JSON format.
        """

        requests.packages.urllib3.disable_warnings()

        request_api_resource = {
            "headers": self.myheaders,
            "verify": self.verify,
            "timeout": timeout,
            "proxies": self.proxies,
        }

        if data is not None:
            if method in [self.methods.DELETE, self.methods.GET]:
                if not isinstance(data, (list, dict, bytes)):
                    raise TypeError(
                        f"'data' type for {method} must be dict, bytes or a list of tuples."
                    )
                request_api_resource["params"] = data
            else:
                if isinstance(data, dict):
                    try:
                        data = json.dumps(data)
                    except Exception:
                        raise TypeError(
                            "Dict provided to 'data' is not json serializable."
                        )
                elif isinstance(data, list):
                    if all(isinstance(item, dict) for item in data):
                        try:
                            data = json.dumps(data)
                        except Exception:
                            raise TypeError(
                                "Dict provided to list in 'data' is not json serializable."
                            )
                elif not isinstance(data, (str, list, bytes, io.TextIOBase)):
                    raise TypeError(
                        f"'data' type for {method} must be str, dict, bytes, file-like or a list of tuples."
                    )

                request_api_resource["data"] = data

        request_api_resource.update(self.kwargs)

        try:
            if method == self.methods.POST:
                r = session.post(
                    self._build_url(resource, ignore_api_path),
                    stream=stream,
                    **request_api_resource,
                )
            elif method == self.methods.PUT:
                r = session.put(
                    self._build_url(resource, ignore_api_path),
                    stream=stream,
                    **request_api_resource,
                )
            elif method == self.methods.PATCH:
                r = session.patch(
                    self._build_url(resource, ignore_api_path),
                    stream=stream,
                    **request_api_resource,
                )
            elif method == self.methods.DELETE:
                r = session.delete(
                    self._build_url(resource, ignore_api_path),
                    stream=stream,
                    **request_api_resource,
                )
            else:
                r = session.get(
                    self._build_url(resource, ignore_api_path),
                    stream=stream,
                    **request_api_resource,
                )

            try:
                if isinstance(r, Response):
                    if return_response_object or stream:
                        return r
                    if r.status_code >= 400:
                        if isinstance(r.text, str):
                            raise requests.exceptions.ConnectionError(
                                r.text, **{"response": r}
                            )
                        else:
                            the_response = json.loads(r.text)
                            raise requests.exceptions.ConnectionError(
                                the_response, **{"response": r}
                            )
                    else:
                        the_response = json.loads(r.text)
                else:
                    the_response = r
            except JSONDecodeError:
                if "content-type" in r.headers:
                    if r.headers["content-type"] == "text/plain":
                        the_response = r.text
                    else:
                        the_response = r
                else:
                    the_response = r

            return the_response
        except requests.exceptions.ConnectionError as err:
            raise
        except Exception as err:
            raise

    def get_session(
        self,
        retries: int = 1,
        backoff_factor: float = 0.3,
        status_forcelist: tuple = (429, 500, 502, 503, 504),
        session=None,
    ) -> requests.Session:
        """
        Method for returning a session object per every requesting thread
        """
        session = session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def call(
        self,
        method: str = None,
        resource: str = None,
        data: dict = None,
        timeout: int = 60,
        return_response_object: bool = False,
        stream: bool = False,
        ignore_api_path: bool = False,
    ) -> Response | str | Any:
        """
        Method for requesting free format api resources
        """
        try:
            with self.get_session() as session:
                result = self._connect(
                    method=method,
                    resource=resource,
                    session=session,
                    data=data,
                    timeout=timeout,
                    return_response_object=return_response_object,
                    stream=stream,
                    ignore_api_path=ignore_api_path,
                )
                return result
        except requests.ConnectionError:
            raise
        except Exception:
            raise

    @property
    def __default_headers(self):
        """
        Property to return the default headers

        :return: Default headers
        :rtype: dict
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
        Method to add a header and set it's value
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
