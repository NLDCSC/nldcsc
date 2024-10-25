import pytest

from nldcsc.plugins.doh.doh_parser import DohParser


class DOHTest:
    def test_doh_request_init(self):
        dp = DohParser()
        assert dp.doh_requester.baseurl == "https://1.1.1.1"
        assert dp.doh_requester.user_agent == "Certex"

    def test_convert_to_reverse_format(self):
        dp = DohParser()
        reversed_format = dp.doh_requester._convert_to_reverse_format("66.102.1.113")
        assert reversed_format == "113.1.102.66.in-addr.arpa"
