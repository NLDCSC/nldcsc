from typing import Any
from uuid import UUID
from sqlalchemy import Dialect, types


class char_UUID(types.TypeDecorator):
    """
    Mysql has no native UUID type, therefore we store it as a CHAR with length 32.
    """

    impl = types.CHAR(32)
    # we user char(32) as types.Uuid excepts a UUID on filter... You cant make partial uuids.

    cache_ok = True

    def process_bind_param(self, value: Any | None, dialect: Dialect) -> Any:
        if not value:
            return value

        if isinstance(value, UUID):
            return value.hex

        return str(value).replace("-", "")

    def process_result_value(self, value: str | None, dialect: Dialect) -> Any | None:
        if value:
            return str(UUID(hex=value))
        return value
