from typing import Any

from typing_extensions import Annotated
from sqlalchemy.orm import mapped_column

# this file should contain all common annotations used:
# - to keep things consistent the naming convention should be <type>_<identifier> -> str_64, str_128, int_pk, etc.

# ints
int_pk = Annotated[int, mapped_column(primary_key=True)]
big_int_pk = Annotated[int, mapped_column(primary_key=True)]

# strings
str_16 = Annotated[str, 16]
str_30 = Annotated[str, 30]
str_50 = Annotated[str, 50]
str_64 = Annotated[str, 64]
str_100 = Annotated[str, 100]
str_128 = Annotated[str, 128]
str_256 = Annotated[str, 256]
str_512 = Annotated[str, 512]
str_text = str

# dicts
dict_json = dict[str, Any]

# lists
list_json = list[Any]

# custom
uuid = Annotated[str, 32]
uuid_pk = Annotated[str, mapped_column(primary_key=True)]
