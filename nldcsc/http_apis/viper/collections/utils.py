from functools import wraps
from typing import Callable, ParamSpec, Type, TypeVar, TYPE_CHECKING

from requests import HTTPError

if TYPE_CHECKING:
    from nldcsc.http_apis.viper.client import ViperClient
    from nldcsc.http_apis.viper.collections.bases import EndpointCollection

T = TypeVar("T")
P = ParamSpec("P")


def as_object(obj: Type[T], transform: Callable[..., T] = None):
    """
    Wrapper to transform a dict into a object.

    Args:
        obj (Type[T]): Object to to transform to.
        transform (Callable[..., T], optional): Method that transforms the dict into the object. Defaults to None.

    Returns:
        Callable[..., Callable[..., T]]: Wrapper that transforms the dict into the object.
    """

    def wrapper(f: Callable[P, dict]) -> Callable[P, T]:
        @wraps(f)
        def inner(*args, **kwargs) -> T:
            r = f(*args, **kwargs)

            try:
                if transform:
                    return transform(r)
                elif hasattr(f, "from_dict") and isinstance(r, dict):
                    return f.from_dict(r)
                return obj(**r)
            except Exception as e:
                raise ValueError(
                    f"Failed transforming response for {f.__name__} into {obj=} -> {e=}"
                )

        return inner

    return wrapper


def refresh_token(client: ViperClient):
    client.auth_info.update_with_response(
        client.v1.auth.refresh_token(refresh_token=client.auth_info.refresh_token)
    )


def get_new_token(client: ViperClient):
    client.auth_info.update_with_response(
        client.v1.auth.login(
            username=client.auth_info.username, password=client.auth_info.password
        )
    )


def get_token(client: ViperClient):
    try:
        if not client.auth_info.refresh_valid():
            raise ValueError

        refresh_token(client)
    except (ValueError, HTTPError) as e:
        if isinstance(e, ValueError) or e.response.status_code == 401:
            get_new_token(client)
        else:
            raise


def requires_login(f):
    @wraps(f)
    def wrapper(self: EndpointCollection, *args, **kwargs):
        auth_info = self.client.auth_info

        if not auth_info.username or not auth_info.password:
            raise ValueError("Cannot call endpoint with unset username and password")

        if not auth_info.valid():
            get_token(self.client)

        try:
            return f(self, *args, **kwargs)
        except HTTPError as e:
            if e.response.status_code != 401:
                raise

        # Try getting a new token as a last effort
        get_new_token(self.client)

        return f(self, *args, **kwargs)

    return wrapper
