from functools import wraps
from typing import Any, Callable, ParamSpec, Type, TypeVar

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
                elif hasattr(obj, "from_dict") and isinstance(r, dict):
                    return obj.from_dict(r)
                return obj(**r)
            except Exception as e:
                raise ValueError(
                    f"Failed transforming response for {f.__name__} into {obj=} -> {e=}"
                )

        return inner

    return wrapper


def signature_of(_: Callable[P, Any]):
    def wrapper(f: Callable[..., T]) -> Callable[P, T]:
        return f

    return wrapper
