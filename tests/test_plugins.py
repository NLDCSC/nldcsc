import pytest

from tests.plugins.doh import DOHTest
from tests.plugins.geoip import GeoIpTest


class TestPlugins(GeoIpTest, DOHTest):
    pass
