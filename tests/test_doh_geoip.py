import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from nldcsc.plugins.doh.doh_parser import (
    AnswerData,
    DohParser,
    QuestionData,
    Request,
    reverse_pointer_ip,
    status_types,
)
from nldcsc.plugins.doh.doh_requester import DOHRequester, q_types
from nldcsc.plugins.geoip.api import GeoIp, GeoIpPaid, TooManyIPAddressesException


def dns_response(data, status_code=200):
    return httpx.Response(status_code, content=json.dumps(data).encode())


def test_reverse_dns_data_models_and_pointer_conversion():
    question = QuestionData(name="1.2.0.192.in-addr.arpa", type=q_types.PTR)
    answer = AnswerData(name="example.test", type=q_types.A, TTL=60, data="192.0.2.1")
    parsed = Request(
        Status=status_types.NOERROR,
        TC=False,
        RD=True,
        RA=True,
        AD=False,
        CD=False,
        Question=[question],
        Answer=[answer],
    )

    assert question.s_type == "PTR"
    assert answer.s_type == "A"
    assert parsed.s_status == "NOERROR"
    assert parsed.request_ok is True
    assert parsed.domain_exists is True
    assert parsed.reverse_data_lookups == ["192.0.2.1"]
    assert reverse_pointer_ip("1.2.0.192.in-addr.arpa") == "192.0.2.1"
    assert reverse_pointer_ip("example.test") is None


def test_reverse_pointer_converts_ipv6_addresses():
    assert reverse_pointer_ip(
        "1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.8.ip6.arpa"
    ) == "8000::1"


def test_doh_requester_builds_queries_and_converts_ptr_records(monkeypatch):
    requester = DOHRequester("https://dns.test")
    requester.a_call = AsyncMock(return_value=["response"])

    async def run():
        ptr = await requester.get_domain_list_by_type(["192.0.2.1"], "PTR")
        bulk = await requester.get_bulk_domains(
            {"A": ["example.test"], q_types.PTR: ["192.0.2.1"]}
        )
        reverse = await requester.get_reverse_lookups(["192.0.2.1"])
        return ptr, bulk, reverse

    ptr, bulk, reverse = asyncio.run(run())
    assert ptr == bulk == reverse == ["response"]
    calls = requester.a_call.await_args_list
    assert calls[0].kwargs["resources"] == [
        "dns-query?name=1.2.0.192.in-addr.arpa&type=12"
    ]
    assert calls[1].kwargs["resources"] == [
        "dns-query?name=example.test&type=1",
        "dns-query?name=1.2.0.192.in-addr.arpa&type=12",
    ]
    assert calls[2].kwargs["resources"] == [
        "dns-query?name=1.2.0.192.in-addr.arpa&type=PTR"
    ]


def test_doh_requester_expands_all_types_and_warns_on_unknown_type(monkeypatch):
    requester = DOHRequester("https://dns.test")
    requester.a_call = AsyncMock(return_value=[])
    warning = Mock()
    monkeypatch.setattr(requester.logger, "warning", warning)

    async def run():
        await requester.get_bulk_domains({"*": ["example.test", "sub.example.test"]})
        await requester.get_domain_list_by_type(["example.test"], "UNKNOWN")

    asyncio.run(run())
    expanded = requester.a_call.await_args_list[0].kwargs["resources"]
    assert len(expanded) == 11
    assert all("type=12" not in value for value in expanded)
    assert requester.a_call.await_args_list[1].kwargs["resources"] == [
        "dns-query?name=example.test&type=UNKNOWN"
    ]
    assert "not in the q_types tuple" in warning.call_args.args[0]


def test_doh_parser_parses_responses_and_skips_malformed_payloads(monkeypatch):
    parser = DohParser()
    warning = Mock()
    monkeypatch.setattr(parser.logger, "warning", warning)
    valid = dns_response(
        {
            "Status": 0,
            "TC": False,
            "RD": True,
            "RA": True,
            "AD": False,
            "CD": False,
            "Question": [{"name": "example.test", "type": 1}],
            "Answer": [{"name": "example.test", "type": 1, "TTL": 10, "data": "192.0.2.1"}],
            "Authority": [],
        }
    )
    malformed = [
        dns_response(["not", "an", "object"]),
        dns_response({"Status": 0}),
        httpx.Response(200, content=b"\xff"),
        dns_response({"Status": 0}, status_code=500),
    ]

    parsed = parser.parse_responses([valid, *malformed])

    assert len(parsed) == 1
    assert parsed[0].Question[0].original_ip is None
    assert parsed[0].reverse_data_lookups == ["192.0.2.1"]
    assert any("yielded fields that could not be parsed" in call.args[0] for call in warning.call_args_list)


def test_doh_parser_performs_forward_and_reverse_requests():
    parser = DohParser()
    forward = dns_response(
        {
            "Status": 0,
            "TC": False,
            "RD": True,
            "RA": True,
            "AD": False,
            "CD": False,
            "Question": [{"name": "example.test", "type": 1}],
            "Answer": [{"name": "example.test", "type": 1, "TTL": 10, "data": "192.0.2.1"}],
        }
    )
    reverse = dns_response(
        {
            "Status": 3,
            "TC": False,
            "RD": True,
            "RA": True,
            "AD": False,
            "CD": False,
            "Question": [],
        }
    )
    parser.doh_requester.get_bulk_domains = AsyncMock(
        side_effect=[[forward], [reverse]]
    )

    result = asyncio.run(parser.request_and_parse({"A": ["example.test"]}))

    assert len(result["forward_requests"]) == 1
    assert len(result["reverse_requests"]) == 1
    assert parser.doh_requester.get_bulk_domains.await_args_list[1].kwargs[
        "workload"
    ] == {q_types.PTR: ["192.0.2.1"]}


def test_geoip_requires_credentials_and_validates_addresses(monkeypatch):
    monkeypatch.delenv("IPGEOLOCATION_ENABLE", raising=False)
    monkeypatch.delenv("IPGEOLOCATION_API_KEY", raising=False)

    with pytest.raises(ValueError, match="API_KEY must be set"):
        GeoIp()

    monkeypatch.setenv("IPGEOLOCATION_ENABLE", "True")
    monkeypatch.setenv("IPGEOLOCATION_API_KEY", "test-key")
    geo = GeoIp()
    assert geo.is_valid_ip("2001:db8::1") is True
    assert geo.is_valid_ip("invalid") is False
    assert isinstance(geo.get_geo_for_ip("invalid"), AttributeError)


def test_geoip_gets_one_ip_and_flag(monkeypatch):
    monkeypatch.setenv("IPGEOLOCATION_ENABLE", "True")
    monkeypatch.setenv("IPGEOLOCATION_API_KEY", "test-key")
    geo = GeoIp()
    geo.call = Mock(return_value={"country_code2": "US"})
    assert geo.get_geo_for_ip("192.0.2.1") == {"country_code2": "US"}
    geo.call.assert_called_once()

    session = Mock()
    session.get.return_value.content = b"flag"
    session_context = Mock()
    session_context.__enter__ = Mock(return_value=session)
    session_context.__exit__ = Mock(return_value=False)
    geo.get_session = Mock(return_value=session_context)
    assert geo.get_country_flag(country_code2="US") == b"flag"
    session.get.assert_called_once_with(
        "https://ipgeolocation.io/static/flags/us_64.png"
    )

    with pytest.raises(ValueError, match="Either ip_address or country_code2"):
        geo.get_country_flag()


def test_geoip_paid_validates_bulk_requests(monkeypatch):
    monkeypatch.setenv("IPGEOLOCATION_ENABLE", "True")
    monkeypatch.setenv("IPGEOLOCATION_API_KEY", "test-key")
    geo = GeoIpPaid()
    geo.call = Mock(return_value=[{"ip": "192.0.2.1"}])

    assert geo.get_geo_for_ip_bulk(["192.0.2.1"]) == [{"ip": "192.0.2.1"}]
    with pytest.raises(AttributeError, match="Wrong IP address"):
        geo.get_geo_for_ip_bulk(["invalid"])
    with pytest.raises(TooManyIPAddressesException, match="exceeds the maximum"):
        geo.get_geo_for_ip_bulk(["192.0.2.1"] * 51)


def test_geoip_fetch_returns_data_and_reports_failures(monkeypatch):
    monkeypatch.setenv("IPGEOLOCATION_ENABLE", "True")
    monkeypatch.setenv("IPGEOLOCATION_API_KEY", "test-key")
    geo = GeoIp()

    class Content:
        async def read(self):
            return b'{"ip":"192.0.2.1","country":"US"}'

    class Response:
        content = Content()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    session = SimpleNamespace(get=Mock(return_value=Response()))
    assert asyncio.run(geo.fetch(session, "https://geo.test")) == {
        "192.0.2.1": {"ip": "192.0.2.1", "country": "US"}
    }

    session.get = Mock(side_effect=RuntimeError("offline"))
    assert asyncio.run(geo.fetch(session, "https://geo.test")) == {
        "ERROR": "Error getting https://geo.test data...."
    }
