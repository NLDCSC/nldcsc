from sqlalchemy import JSON, TEXT, BigInteger, String
from sqlalchemy.orm import DeclarativeBase, registry

from .annotations import (
    str_16,
    str_30,
    str_32,
    str_50,
    str_64,
    str_100,
    str_128,
    str_256,
    str_512,
    str_text,
    list_json,
    dict_json,
    big_int,
    big_int_pk,
    uuid,
    uuid_pk,
)
from .custom_types import char_UUID


class ModelBase(DeclarativeBase):
    registry = registry(
        type_annotation_map={
            str_16: String(16),
            str_30: String(30),
            str_32: String(32),
            str_50: String(50),
            str_64: String(64),
            str_100: String(100),
            str_128: String(128),
            str_256: String(256),
            str_512: String(512),
            str_text: TEXT,
            dict_json: JSON,
            list_json: JSON,
            big_int_pk: BigInteger,
            big_int: BigInteger,
            uuid: char_UUID,
            uuid_pk: char_UUID,
        },
    )
