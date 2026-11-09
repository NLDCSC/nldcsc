from unittest.mock import Mock

import pytest
import requests
from requests.exceptions import JSONDecodeError
from requests_cache.backends import SQLiteCache

from nldcsc.http_apis.base_class.cached_base_class import CachedAPI


class FakeResponse:
    ok = True
    text = "plain response"

    def json(self):
        return {"ok": True}

    def raise_for_status(self):
        raise requests.HTTPError("bad response")


class FakeSession:
    def __init__(self, response=None):
        self.response = response or FakeResponse()
        self.get = Mock(return_value=self.response)
        self.post = Mock(return_value=self.response)
        self.close = Mock()
        self.verify = None
        self.proxies = {}


def test_cached_api_builds_urls_and_manages_headers():
    api = CachedAPI(
        "https://example.test/",
        api_path="/v1/",
        user_agent="TestAgent",
        proxies={"https": "http://proxy.test"},
    )

    assert api.build_url("/items") == "https://example.test/v1/items"
    assert api.build_url("items", ignore_api_path=True) == "https://example.test/items"
    assert api.build_url(None) == "https://example.test/v1"
    assert api.headers == {"User-Agent": "TestAgent"}

    api.set_header("X-Test", "yes")
    api.del_header("X-Test")
    assert api.headers == {"User-Agent": "TestAgent"}
    api.clear_headers()
    assert api.headers == {}
    api.reset_headers()
    assert api.headers == {"User-Agent": "TestAgent"}


def test_call_merges_request_options_and_unpacks_response(monkeypatch):
    api = CachedAPI(
        "https://example.test",
        api_path="v1",
        headers={"X-Default": "default"},
        timeout=17,
    )
    session = FakeSession()
    monkeypatch.setattr(api, "get_session", Mock(return_value=session))

    result = api.call(
        api.methods.GET,
        "/items",
        headers={"X-Request": "request"},
        params={"page": 2},
    )

    assert result == {"ok": True}
    session.get.assert_called_once_with(
        "https://example.test/v1/items",
        timeout=17,
        headers={"User-Agent": "CachedApi", "X-Request": "request"},
        params={"page": 2},
    )


def test_call_context_options_override_defaults_and_unpacked_response(monkeypatch):
    api = CachedAPI("https://example.test", persist_self=False)
    session = FakeSession()
    monkeypatch.setattr(api, "get_session", Mock(return_value=session))

    with api.override_request_options(timeout=3, headers={"X-Context": "yes"}):
        response = api.call(
            api.methods.POST,
            "items",
            unpack_response=False,
            timeout=9,
            headers={"X-Call": "yes"},
        )

    assert response is session.response
    session.post.assert_called_once_with(
        "https://example.test/items",
        timeout=9,
        headers={"User-Agent": "CachedApi", "X-Call": "yes"},
    )
    session.close.assert_called_once()


def test_bypass_cache_sets_no_cache_header():
    api = CachedAPI("https://example.test")

    with api.bypass_cache():
        assert api._request_kwargs.get() == {"headers": {"Cache-Control": "no-cache"}}

    with pytest.raises(LookupError):
        api._request_kwargs.get()


def test_session_options_and_lru_persistence():
    api = CachedAPI("https://example.test", max_sessions=1)
    backend = SQLiteCache(":memory:")

    with api.override_session_options(expire_after=30, cache_control=False):
        first = api.get_session(backend=backend)
        first.close = Mock(wraps=first.close)
        assert first.expire_after == 30
        assert api.get_session(backend=backend) is first

    other_backend = SQLiteCache(":memory:")
    second = api.get_session(backend=other_backend)
    first.close.assert_called_once()
    assert len(api.sessions) == 1
    assert next(iter(api.sessions.values())) is second

    second.close = Mock(wraps=second.close)
    api.close()
    second.close.assert_called_once()


def test_recreating_a_persisted_session_closes_old_instance():
    api = CachedAPI("https://example.test")
    backend = SQLiteCache(":memory:")

    first = api.get_session(backend=backend)
    first.close = Mock(wraps=first.close)
    second = api.get_session(backend=backend, force_recreate=True)

    first.close.assert_called()
    assert second is not first
    api.close()


def test_unknown_method_and_failed_response_are_reported(monkeypatch):
    api = CachedAPI("https://example.test")
    session = FakeSession()
    monkeypatch.setattr(api, "get_session", Mock(return_value=session))

    with pytest.raises(ValueError, match="Unknown method"):
        api.call("TRACE", "items")

    response = Mock(ok=False)
    response.raise_for_status.side_effect = requests.HTTPError("bad response")
    with pytest.raises(requests.HTTPError, match="bad response"):
        api.unpack_response(response)

    json_error = JSONDecodeError("invalid json", "bad", 0)
    response = Mock(ok=True, text="plain")
    response.json.side_effect = json_error
    assert api.unpack_response(response) == "plain"
