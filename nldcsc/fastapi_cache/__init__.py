import hashlib
from typing import ClassVar, Optional, Type, Any, Callable, Protocol, Awaitable, Union

from starlette.requests import Request
from starlette.responses import Response

from viper.core.fastapi_cache.backends.base import Backend
from viper.core.fastapi_cache.coder import Coder, JsonCoder

__all__ = [
    "FastAPICache",
    "KeyBuilder",
    "default_key_builder",
]


def default_key_builder(
    func: Callable[..., Any],
    namespace: str = "",
    *,
    request: Optional[Request] = None,
    response: Optional[Response] = None,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> str:
    cache_key = hashlib.md5(  # noqa: S324
        f"{func.__module__}:{func.__name__}:{args}:{kwargs}".encode()
    ).hexdigest()
    return f"{namespace}:{cache_key}"


class KeyBuilder(Protocol):
    def __call__(
        self,
        __function: Callable[..., Any],
        __namespace: str = ...,
        *,
        request: Optional[Request] = ...,
        response: Optional[Response] = ...,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Union[Awaitable[str], str]: ...


class FastAPICache:
    _backend: ClassVar[Optional[Backend]] = None
    _prefix: ClassVar[Optional[str]] = None
    _expire: ClassVar[Optional[int]] = None
    _init: ClassVar[bool] = False
    _coder: ClassVar[Optional[Type[Coder]]] = None
    _key_builder: ClassVar[Optional[KeyBuilder]] = None
    _cache_status_header: ClassVar[Optional[str]] = None
    _enable: ClassVar[bool] = True

    @classmethod
    def init(
        cls,
        backend: Backend,
        prefix: str = "",
        expire: Optional[int] = None,
        coder: Type[Coder] = JsonCoder,
        key_builder: KeyBuilder = default_key_builder,
        cache_status_header: str = "X-Cache",
        enable: bool = True,
    ) -> None:
        if cls._init:
            return
        cls._init = True
        cls._backend = backend
        cls._prefix = prefix
        cls._expire = expire
        cls._coder = coder
        cls._key_builder = key_builder
        cls._cache_status_header = cache_status_header
        cls._enable = enable

    @classmethod
    def reset(cls) -> None:
        cls._init = False
        cls._backend = None
        cls._prefix = None
        cls._expire = None
        cls._coder = None
        cls._key_builder = None
        cls._cache_status_header = None
        cls._enable = True

    @classmethod
    def get_backend(cls) -> Backend:
        return cls._backend

    @classmethod
    def get_prefix(cls) -> str:
        return cls._prefix

    @classmethod
    def get_expire(cls) -> Optional[int]:
        return cls._expire

    @classmethod
    def get_coder(cls) -> Type[Coder]:
        return cls._coder

    @classmethod
    def get_key_builder(cls) -> KeyBuilder:
        return cls._key_builder

    @classmethod
    def get_cache_status_header(cls) -> str:
        return cls._cache_status_header

    @classmethod
    def get_enable(cls) -> bool:
        return cls._enable

    @classmethod
    async def clear(
        cls, namespace: Optional[str] = None, key: Optional[str] = None
    ) -> int:
        namespace = f'{cls._prefix}:{namespace if namespace else ""}'
        return await cls.get_backend.clear(namespace, key)
