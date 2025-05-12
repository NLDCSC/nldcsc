from collections import namedtuple
from datetime import date, datetime
import os
from json import JSONDecodeError
import re

import pytest

from nldcsc.generic.utils import (
    getenv_dict,
    getenv_bool,
    getenv_list,
    str2bool,
    generate_random_password,
    getenv_choice,
    getenv_str,
    reverse_from_named_tuple,
    _true_set,
    _false_set,
    __MANDATORY_VALUE__,
)

from nldcsc.generic.times import (
    timestampTOcalendarattrs,
    timestampTOdatestring,
    timestampTOdatetime,
    timestampTOdatetimestring,
    timestringTOdatetimestring,
    timestringTOtimestamp,
    datetimeTOtimestamp,
    dateTOtimestamp,
)


class TestGenericUtils:

    def test_get_env_str(self):
        ENV_VAL = "NLDCSC"
        ENV_KEY = "TEST_STR_ENV"

        os.environ[ENV_KEY] = ENV_VAL

        assert getenv_str(ENV_KEY) == ENV_VAL

    def test_get_env_str_missing(self):
        ENV_KEY = "TEST_STR_ENV"

        if ENV_KEY in os.environ:
            del os.environ[ENV_KEY]

        assert getenv_str(ENV_KEY) is None
        assert getenv_str(ENV_KEY, "DEFAULT") == "DEFAULT"

    def test_get_env_str_mandatory(self):
        ENV_VAL = "NLDCSC"
        ENV_KEY = "TEST_STR_ENV"

        os.environ[ENV_KEY] = ENV_VAL

        assert getenv_str(ENV_KEY, mandatory=True) == ENV_VAL

    def test_get_env_str_mandatory_missing(self):
        ENV_KEY = "TEST_STR_ENV"

        os.environ[ENV_KEY] = __MANDATORY_VALUE__

        with pytest.raises(ValueError, match=f"{ENV_KEY} is not set!"):
            getenv_str(ENV_KEY, mandatory=True)

    def test_get_env_choice(self):
        ENV_VAL = "YES"
        ENV_KEY = "TEST_STR_ENV"
        CHOICES = [ENV_VAL, "NO"]

        os.environ[ENV_KEY] = ENV_VAL

        assert getenv_choice(ENV_KEY, CHOICES) == ENV_VAL

    def test_get_env_choice_invalid(self):
        ENV_VAL = "1234"
        ENV_KEY = "TEST_STR_ENV"
        CHOICES = ["YES", "NO"]

        os.environ[ENV_KEY] = ENV_VAL

        with pytest.raises(
            ValueError,
            match=f"The variable {ENV_KEY} is not set to a valid choice, choices are {re.escape(str(CHOICES))}!",
        ):
            getenv_choice(ENV_KEY, CHOICES)

    def test_get_env_choice_mandatory(self):
        ENV_VAL = "YES"
        ENV_KEY = "TEST_STR_ENV"
        CHOICES = [ENV_VAL, "NO"]

        os.environ[ENV_KEY] = ENV_VAL

        assert getenv_choice(ENV_KEY, CHOICES, mandatory=True) == ENV_VAL

    def test_get_env_choice_mandatory_missing(self):
        ENV_KEY = "TEST_STR_ENV"
        CHOICES = ["YES", "NO"]

        os.environ[ENV_KEY] = __MANDATORY_VALUE__

        with pytest.raises(ValueError, match=f"{ENV_KEY} is not set!"):
            getenv_choice(ENV_KEY, CHOICES, mandatory=True)

    def test_get_env_choice_mandatory_invalid(self):
        ENV_KEY = "TEST_STR_ENV"
        CHOICES = [__MANDATORY_VALUE__, "NO"]

        os.environ[ENV_KEY] = __MANDATORY_VALUE__

        with pytest.raises(ValueError, match=f"{ENV_KEY} is not set!"):
            getenv_choice(ENV_KEY, CHOICES, mandatory=True)

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

    def test_str_to_bool_invalid(self):
        VALS = ("1234", 1, True, 1.3, [], (), {})

        for v in VALS:
            with pytest.raises(
                ValueError,
                match=f'Expected "{", ".join(_true_set | _false_set)}" -> received "{re.escape(str(v))}"',
            ):
                str2bool(v)

    def test_str_to_bool_invalid_no_raise(self):
        VALS = ("1234", 1, True, 1.3, [], (), {})

        for v in VALS:
            assert str2bool(v, False) is None

    def test_random_password_generator(self):
        assert len(generate_random_password()) == 32

    def test_reverse_from_named_tuple(self):
        test_tuple = namedtuple("test_tuple", ("A", "B", "C", "D"))(0, 1, "2", "3")

        assert reverse_from_named_tuple(test_tuple, 0) == "A"
        assert reverse_from_named_tuple(test_tuple, 1) == "B"
        assert reverse_from_named_tuple(test_tuple, "2") == "C"
        assert reverse_from_named_tuple(test_tuple, "3") == "D"

    def test_reverse_from_named_tuple_missing(self):
        test_tuple = namedtuple("test_tuple", ("A", "B"))(0, 1)

        with pytest.raises(
            KeyError,
            match=f"The requested index does not exist! Choices are {re.escape(str({0: 'A', 1: 'B'}))}",
        ):
            reverse_from_named_tuple(test_tuple, 3)


class TestGenericTimes:
    def test_timestringTOtimestamp(self):
        times = (
            ("12-05-2025", 1747008000),
            ("12-05-2025 14:45", 1747061100),
            ("2025-05-12 14:45:30", 1747061130),
            ("14:45:30 12-05-2025", 1747061130),
            ("2025-05-12", 1747008000),
            ("2025-05-12 14:45:30 UTC", 1747061130),
            ("2025-05-12T14:45:30", 1747061130),
            ("2025-05-12T14:45:30Z", 1747061130),
            ("2025-05-12T14:45:30+0000", 1747061130),
            ("2025-05-12T14:45:30.123456", 1747061130),
            ("2025-05-12T14:45:30,123456", 1747061130),
            ("2025-05-12T14:45:30.123456Z", 1747061130),
            ("2025-05-12T14:45:30,123456Z", 1747061130),
            ("2025-05-12T14:45:30.123456Z+0000", 1747061130),
            ("2025-05-12T14:45:30,123456Z+0000", 1747061130),
            ("2025-05-12 14:45:30.123456+0000", 1747061130),
        )

        for time, value in times:
            assert timestringTOtimestamp(time) == value

    def test_timestringTOtimestamp_invalid(self):
        time = "INVALID"

        assert timestringTOtimestamp(time) is False

    def test_datetimeToTimestamp(self):
        time = datetime(
            year=2025, month=5, day=12, hour=14, minute=45, second=30, microsecond=0
        )

        assert datetimeTOtimestamp(time) == 1747061130

    def test_dateTOtimestamp(self):
        time = date(year=2025, month=5, day=12)

        assert dateTOtimestamp(time) == 1747008000

    def test_timestampTOdatetime(self):
        time = 1747061130

        assert timestampTOdatetime(time) == datetime(
            year=2025, month=5, day=12, hour=14, minute=45, second=30, microsecond=0
        )

    def test_timestampTOdatetimestring(self):
        time = 1747061130

        assert timestampTOdatetimestring(time, vis=True) == "2025-05-12 14:45:30"
        assert timestampTOdatetimestring(time) == "2025-05-12T14:45:30Z"

    def test_timestampTOcalendarattrs(self):
        time = 1747061130

        assert timestampTOcalendarattrs(time) == {
            "day": "12",
            "month": "May",
            "weekday": "Monday",
        }

    def test_timestampTOdatestring(self):
        time = 1747061130

        assert timestampTOdatestring(time) == "12-05-2025"

    def test_timestringTOdatetimestring(self):
        time = "2025-05-12 14:45:30.123456+0000"

        assert timestringTOdatetimestring(time) == "2025-05-12T14:45:30Z"

    def test_timestringTOdatetimestring_invalid(self):
        time = "INVALID"

        assert timestringTOdatetimestring(time) is False
