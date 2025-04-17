import ast
import collections
import json
import os
import secrets
import string
from json import JSONDecodeError

__MANDATORY_VALUE__ = "<<MANDATORY_VALUE>>"


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


def getenv_str(name: str, default: str = None, mandatory: bool = False):
    raw = os.getenv(name, default)

    if mandatory:
        if raw == __MANDATORY_VALUE__:
            raise ValueError(f"{name} is not set!")

    return raw


def getenv_choice(
    name: str, choices: list[str], default: str = None, mandatory: bool = False
):
    raw = os.getenv(name, default)

    if mandatory:
        if raw == __MANDATORY_VALUE__:
            raise ValueError(f"{name} is not set!")

    if raw not in choices:
        raise ValueError(
            f"The variable {name} is not set to a valid choice, choices are {choices}!"
        )

    return raw


_true_set = {"yes", "true", "t", "y", "1"}
_false_set = {"no", "false", "f", "n", "0"}


def str2bool(value, raise_exc=True):
    if isinstance(value, str):
        value = value.lower()
        if value in _true_set:
            return True
        if value in _false_set:
            return False

    if raise_exc:
        raise ValueError(
            f'Expected "{", ".join(_true_set | _false_set)}" -> received "{value}"'
        )
    return None


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
