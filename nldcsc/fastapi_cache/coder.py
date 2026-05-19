import datetime
import json
import pickle  # nosec:B403
from decimal import Decimal
from typing import (
    Any,
    ClassVar,
    Dict,
    Optional,
    TypeVar,
    Union,
    overload,
)

from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from starlette.templating import (
    _TemplateResponse as TemplateResponse,  # pyright: ignore[reportPrivateUsage]
)


class ModelField:
    pass


_T = TypeVar("_T", bound=type)


class JsonEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime.datetime):
            return {"val": str(o), "_spec_type": "datetime"}
        elif isinstance(o, datetime.date):
            return {"val": str(o), "_spec_type": "date"}
        elif isinstance(o, Decimal):
            return {"val": str(o), "_spec_type": "decimal"}
        else:
            return jsonable_encoder(o)


class Coder:
    @classmethod
    def encode(cls, value: Any) -> bytes:
        raise NotImplementedError

    @classmethod
    def decode(cls, value: bytes) -> Any:
        raise NotImplementedError

    # (Shared) cache for endpoint return types to Pydantic model fields.
    # Note that subclasses share this cache! If a subclass overrides the
    # decode_as_type method and then stores a different kind of field for a
    # given type, do make sure that the subclass provides its own class
    # attribute for this cache.
    _type_field_cache: ClassVar[Dict[Any, ModelField]] = {}

    @overload
    @classmethod
    def decode_as_type(cls, value: bytes, *, type_: _T) -> _T: ...

    @overload
    @classmethod
    def decode_as_type(cls, value: bytes, *, type_: None) -> Any: ...

    @classmethod
    def decode_as_type(cls, value: bytes, *, type_: Optional[_T]) -> Union[_T, Any]:
        """Decode value to the specific given type

        The default implementation uses the Pydantic model system to convert the value.

        """
        result = cls.decode(value)
        return result


class JsonCoder(Coder):
    @classmethod
    def encode(cls, value: Any) -> Any:
        if isinstance(value, JSONResponse):
            return value.body
        return json.dumps(value, cls=JsonEncoder).encode()

    @classmethod
    def decode(cls, value: bytes) -> Any:
        # explicitly decode from UTF-8 bytes first, as otherwise
        # json.loads() will first have to detect the correct UTF-
        # encoding used.
        return json.loads(value.decode())


class PickleCoder(Coder):
    @classmethod
    def encode(cls, value: Any) -> bytes:
        if isinstance(value, TemplateResponse):
            value = value.body
        return pickle.dumps(value)

    @classmethod
    def decode(cls, value: bytes) -> Any:
        return pickle.loads(value)  # noqa: S301

    @classmethod
    def decode_as_type(cls, value: bytes, *, type_: Optional[_T]) -> Any:
        # Pickle already produces the correct type on decoding, no point
        # in paying an extra performance penalty for pydantic to discover
        # the same.
        return cls.decode(value)
