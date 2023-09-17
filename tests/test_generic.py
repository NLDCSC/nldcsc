import os
from json import JSONDecodeError

import pytest

from nldcsc.generic.utils import (
    getenv_dict,
    getenv_bool,
    getenv_list,
    str2bool,
    generate_random_password,
)


class TestGeneric:
    def test_get_env_dict(self):
        os.environ["DICT_ENV"] = '{"key1": "value1", "key2": "value2"}'
        os.environ["DICT_ENV_ERROR"] = "{'key1': 'value1', 'key2': 'value2'}"

        env_dict = getenv_dict("DICT_ENV", {"key": "default"})

        assert isinstance(env_dict, dict)
        assert env_dict["key1"] == "value1"

        env_dict = getenv_dict("DICT_ENV_NON_EXISTENT", {"key": "default"})

        assert isinstance(env_dict, dict)
        assert env_dict["key"] == "default"

        env_dict = getenv_dict("DICT_ENV_NON_EXISTENT")

        assert isinstance(env_dict, dict)
        assert len(env_dict) == 0

        with pytest.raises(JSONDecodeError):
            getenv_dict("DICT_ENV_ERROR", {"key": "default"})

    def test_get_env_list(self):
        os.environ["LIST_ENV"] = '["value1", "value2"]'
        os.environ["LIST_ENV_ERROR"] = "['value1', 'value2']"

        env_list = getenv_list("LIST_ENV", ["default"])

        assert isinstance(env_list, list)
        assert env_list[0] == "value1"

        env_list = getenv_list("LIST_ENV_NON_EXISTENT", ["default"])

        assert isinstance(env_list, list)
        assert env_list[0] == "default"

        env_list = getenv_list("LIST_ENV_NON_EXISTENT")

        assert isinstance(env_list, list)
        assert len(env_list) == 0

        with pytest.raises(JSONDecodeError):
            getenv_list("LIST_ENV_ERROR", ["default"])

    def test_get_env_bool(self):
        os.environ["BOOL_ENV_TRUE"] = "True"
        os.environ["BOOL_ENV_FALSE"] = "False"
        os.environ["BOOL_ENV_ERROR"] = "Blerf"
        os.environ["BOOL_ENV_DICT"] = '{"key1": "value1", "key2": "value2"}'

        env_bool = getenv_bool("BOOL_ENV_TRUE", "False")
        env_bool_false = getenv_bool("BOOL_ENV_FALSE", "False")

        assert isinstance(env_bool, bool)
        assert env_bool is True
        assert env_bool_false is False

        env_bool = getenv_bool("BOOL_ENV_NON_EXISTENT", "False")

        assert isinstance(env_bool, bool)
        assert env_bool is False

        with pytest.raises(ValueError):
            getenv_bool("BOOL_ENV_ERROR", "False")

        with pytest.raises(ValueError):
            getenv_bool("BOOL_ENV_DICT", "False")

    def test_str_to_bool(self):
        choices = {"yes", "true", "1"}

        assert str2bool(choices.pop()) is True
        assert str2bool("false") is False

    def test_random_password_generator(self):
        assert len(generate_random_password()) == 32
