import asyncio

import httpx
import pytest

from nldcsc.httpx_apis.base_class.httpx_base_class import HttpxBaseClass


@pytest.fixture
def api():
    return HttpxBaseClass("https://example.test", use_async_client=False)


def test_initialization_and_header_management(api):
    assert api._build_url("items") == "https://example.test/items"
    assert api.headers == {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "HttpxBaseClass",
    }

    api.set_header_field("X-Test", "yes")
    assert api.del_header_field("X-Test") == api.headers
    api.clear_headers()
    assert api.headers is None
    api.set_header_field("X-Test", "yes")
    api.reset_headers()
    assert "X-Test" not in api.headers


def test_api_path_proxy_options_and_invalid_proxy():
    api = HttpxBaseClass(
        "https://example.test",
        api_path="v1",
        proxies={"http": "http://proxy.test:8080", "https": "http://secure-proxy.test"},
        verify=True,
        follow_redirects=False,
        http2=False,
    )
    assert api._build_url("items") == "https://example.test/v1/items"
    assert str(api.proxies) == "http://secure-proxy.test"
    assert api.verify is True
    assert api.follow_redirects is False
    assert api.http2 is False

    with pytest.raises(ValueError, match="must contain http or https"):
        HttpxBaseClass("https://example.test", proxies={"ftp": "proxy"})


def test_sync_call_handles_single_list_generic_and_stream_resources(monkeypatch, api):
    def handler(request):
        return httpx.Response(200, json={"url": str(request.url)}, request=request)

    monkeypatch.setattr(
        api,
        "get_client",
        lambda: httpx.Client(transport=httpx.MockTransport(handler)),
    )

    one = api.call("GET", "one")
    many = api.call("GET", ["one", "two"])
    generic = api.call("GET", "generic", generic_request=True)
    streamed = api.call("GET", "https://example.test/stream", stream=True)

    assert one.json()["url"] == "https://example.test/one"
    assert [response.json()["url"] for response in many] == [
        "https://example.test/one",
        "https://example.test/two",
    ]
    assert generic.json()["url"] == "https://example.test/generic"
    assert b"https://example.test/stream" in streamed


def test_sync_call_sends_body_and_rejects_get_mapping(monkeypatch, api):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, request=request)

    monkeypatch.setattr(
        api,
        "get_client",
        lambda: httpx.Client(transport=httpx.MockTransport(handler)),
    )

    api.call("POST", "items", data={"name": "item"})
    assert seen[0].read() == b"name=item"

    with pytest.raises(TypeError, match="data == bytes"):
        api.call("GET", "items", data={"page": 1})

    api.call("GET", "items", data=b"payload", generic_request=True)
    assert seen[1].read() == b"payload"


def test_sync_call_propagates_http_errors(monkeypatch, api):
    def handler(request):
        raise httpx.ConnectError("offline", request=request)

    monkeypatch.setattr(
        api,
        "get_client",
        lambda: httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(httpx.ConnectError, match="offline"):
        api.call("GET", "items")


def test_async_call_supports_single_and_multiple_resources(monkeypatch):
    api = HttpxBaseClass("https://example.test")

    def handler(request):
        return httpx.Response(200, json={"url": str(request.url)}, request=request)

    monkeypatch.setattr(
        api,
        "get_client",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    async def run():
        one = await api.a_call("GET", "one")
        many = await api.a_call("GET", ["one", "two"])
        generic = await api.a_call("GET", "generic", generic_request=True)
        return one, many, generic

    one, many, generic = asyncio.run(run())
    assert one.json()["url"] == "https://example.test/one"
    assert [response.json()["url"] for response in many] == [
        "https://example.test/one",
        "https://example.test/two",
    ]
    assert generic.json()["url"] == "https://example.test/generic"


def test_async_call_rejects_mapping_as_get_body(monkeypatch):
    api = HttpxBaseClass("https://example.test")
    monkeypatch.setattr(
        api,
        "get_client",
        lambda: httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, request=request)
            )
        ),
    )

    async def run():
        with pytest.raises(TypeError, match="data == bytes"):
            await api.a_call("GET", "items", data={"page": 1})

    asyncio.run(run())
