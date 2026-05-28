import logging
from functools import wraps
from inspect import Parameter, isawaitable, iscoroutinefunction
from typing import (
    Awaitable,
    Callable,
    Optional,
    Type,
    TypeVar,
    Union,
    ParamSpec,
)

from fastapi import Depends
from fastapi.concurrency import run_in_threadpool
from fastapi.dependencies.utils import (
    get_typed_return_annotation,
    get_typed_signature,
)
from nldcsc.fastapi_cache import FastAPICache, KeyBuilder
from nldcsc.fastapi_cache.coder import Coder
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_304_NOT_MODIFIED

logger: logging.Logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

P = ParamSpec("P")
R = TypeVar("R")


def get_request(request: Request):
    yield request


def get_response(response: Response):
    yield response


def _uncacheable(request: Optional[Request]) -> bool:
    """Determine if this request should not be cached

    Returns true if:
    - Caching has been disabled globally
    - This is not a GET request
    - The request has a Cache-Control header with a value of "no-store"

    """
    if not FastAPICache.get_enable():
        return True
    if request is None:
        return False
    if request.method != "GET":
        return True
    return request.headers.get("Cache-Control") == "no-store"


def fastapi_cache(
    expire: Optional[int] = None,
    coder: Optional[Type[Coder]] = None,
    key_builder: Optional[KeyBuilder] = None,
    namespace: str = "",
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[Union[R, Response]]]]:
    def wrapper(
        func: Callable[P, Awaitable[R]],
    ) -> Callable[P, Awaitable[Union[R, Response]]]:

        wrapped_signature = get_typed_signature(func)

        parameters = list(wrapped_signature.parameters.values())

        for i, param in enumerate(parameters):
            if param.kind == param.VAR_POSITIONAL:
                break
            if param.kind == param.VAR_KEYWORD:
                break
        else:
            i = len(parameters)

        req_name = "request"
        req_present = req_name in wrapped_signature.parameters

        res_name = "response"
        res_present = res_name in wrapped_signature.parameters

        if not req_present:
            new_request_param = Parameter(
                name=req_name,
                annotation=Request,
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=Depends(get_request),
            )
            parameters.insert(i, new_request_param)

        if not res_present:
            new_response_param = Parameter(
                name=res_name,
                annotation=Response,
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=Depends(get_response),
            )
            parameters.insert(i, new_response_param)

        return_type = get_typed_return_annotation(func)
        new_signature = wrapped_signature.replace(
            parameters=parameters, return_annotation=return_type
        )

        @wraps(func)
        async def inner(*args: P.args, **kwargs: P.kwargs) -> Union[R, Response]:
            nonlocal coder
            nonlocal expire
            nonlocal key_builder

            async def ensure_async_func(*args: P.args, **kwargs: P.kwargs) -> R:
                """Run cached sync functions in thread pool just like FastAPI."""
                # if the wrapped function does NOT have request or response in
                # its function signature, make sure we don't pass them in as
                # keyword arguments
                if not req_present:
                    kwargs.pop(req_name, None)
                if not res_present:
                    kwargs.pop(res_name, None)

                if iscoroutinefunction(func):
                    # async, return as is.
                    # unintuitively, we have to await once here, so that caller
                    # does not have to await twice. See
                    # https://stackoverflow.com/a/59268198/532513
                    return await func(*args, **kwargs)
                else:
                    # sync, wrap in thread and return async
                    # see above why we have to await even though caller also awaits.
                    return await run_in_threadpool(func, *args, **kwargs)  # type: ignore[arg-type]

            copy_kwargs = kwargs.copy()
            request: Optional[Request] = copy_kwargs.pop(req_name, None)  # type: ignore[assignment]
            response: Optional[Response] = copy_kwargs.pop(res_name, None)  # type: ignore[assignment]

            if _uncacheable(request):
                return await ensure_async_func(*args, **kwargs)

            prefix = FastAPICache.get_prefix()
            coder = coder or FastAPICache.get_coder()
            expire = expire or FastAPICache.get_expire()
            key_builder = key_builder or FastAPICache.get_key_builder()
            backend = FastAPICache.get_backend()
            cache_status_header = FastAPICache.get_cache_status_header()

            cache_key = key_builder(
                func,
                f"{prefix}:{namespace}",
                request=request,
                response=response,
                args=args,
                kwargs=copy_kwargs,
            )
            if isawaitable(cache_key):
                cache_key = await cache_key

            try:
                ttl, cached = await backend.get_with_ttl(cache_key)
            except Exception as e:
                logger.warning(
                    f"Error retrieving cache key '{cache_key}' from backend -> {e}",
                    exc_info=True,
                )
                ttl, cached = 0, None

            if cached is None or (
                request is not None
                and request.headers.get("Cache-Control") == "no-cache"
            ):  # cache miss
                result = await ensure_async_func(*args, **kwargs)
                to_cache = coder.encode(result)

                try:
                    await backend.set(cache_key, to_cache, expire)
                except Exception:
                    logger.warning(
                        f"Error setting cache key '{cache_key}' in backend:",
                        exc_info=True,
                    )

                if response:
                    response.headers.update(
                        {
                            "Cache-Control": f"max-age={expire}",
                            "ETag": f"W/{hash(to_cache)}",
                            cache_status_header: "MISS",
                        }
                    )

            else:  # cache hit
                if response:
                    etag = f"W/{hash(cached)}"
                    response.headers.update(
                        {
                            "Cache-Control": f"max-age={ttl}",
                            "ETag": etag,
                            cache_status_header: "HIT",
                        }
                    )

                    if_none_match = request and request.headers.get("if-none-match")
                    if if_none_match == etag:
                        response.status_code = HTTP_304_NOT_MODIFIED
                        return response

                result = coder.decode_as_type(cached, type_=return_type)

            return result

        inner.__signature__ = new_signature

        return inner

    return wrapper
