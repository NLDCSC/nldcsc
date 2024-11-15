import ast
import collections
import json
import os
import secrets
import string
from json import JSONDecodeError


def getenv_bool(name: str, default: str = "False"):
    raw = os.getenv(name, default).title()
    try:
        the_bool = ast.literal_eval(raw)

        if not isinstance(the_bool, bool):
            raise ValueError
    except ValueError:
        raise

    return the_bool


def getenv_list(name: str, default: list = None):
    if default is None:
        default = []

    raw = os.getenv(name, default)

    if not isinstance(raw, list):
        try:
            the_list = json.loads(raw.replace("\n", ""))
            return the_list
        except JSONDecodeError:
            raise

    return default


def getenv_dict(name: str, default: dict = None):
    if default is None:
        default = {}

    raw = os.getenv(name, default)

    if not isinstance(raw, dict):
        try:
            the_dict = json.loads(raw)
            return the_dict
        except JSONDecodeError:
            raise

    return default


def str2bool(v):
    return v.lower() in ("yes", "true", "1")


def generate_random_password():
    # define the alphabet
    letters = string.ascii_letters
    digits = string.digits

    alphabet = letters + digits

    # fix password length
    pwd_length = 32

    # generate a password string
    pwd = ""
    for _ in range(pwd_length):
        pwd += "".join(secrets.choice(alphabet))

    return pwd


def reverse_from_named_tuple(
    n_tuple: collections.namedtuple, index: int | str, lowercase_output: bool = False
) -> str:
    n_list = [
        x.lower() if lowercase_output else x
        for x in n_tuple.__dir__()
        if not x.startswith("_") and x not in ["index", "count"]
    ]

    n_rev_types = {getattr(n_tuple, x.upper()): x for x in n_list}

    try:
        return n_rev_types[index]
    except KeyError:
        raise KeyError(f"The requested index does not exist! Choices are {n_rev_types}")


def exclude_optional_dict(value):
    return value is None or not value
