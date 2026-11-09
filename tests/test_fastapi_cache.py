import asyncio
import datetime
from decimal import Decimal

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from nldcsc.fastapi_cache import FastAPICache, default_key_builder
from nldcsc.fastapi_cache.coder import Coder, JsonCoder, PickleCoder
from nldcsc.fastapi_cache.decorator import fastapi_cache


class MemoryBackend:
    def __init__(self):
        self.values = {}
        self.get_error = None
        self.set_error = None

    async def get_with_ttl(self, key):
        if self.get_error:
            raise self.get_error
        return 10, self.values.get(key)

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value, expire=None):
        if self.set_error:
            raise self.set_error
        self.values[key] = value

    async def clear(self, namespace=None, key=None):
        if key:
            return int(self.values.pop(key, None) is not None)
        keys = [name for name in self.values if name.startswith(namespace or "")]
        for name in keys:
            del self.values[name]
        return len(keys)


def make_request(method="GET", headers=()):
    return Request(
        {
            "type": "http",
            "method": method,
            "path": "/",
            "headers": list(headers),
            "query_string": b"",
            "server": ("testserver", 80),
            "client": ("127.0.0.1", 1234),
            "scheme": "http",
            "http_version": "1.1",
        }
    )


def setup_function():
    FastAPICache.reset()


def teardown_function():
    FastAPICache.reset()


def test_json_coder_handles_special_types_and_response():
    value = {
        "date": datetime.date(2025, 5, 12),
        "datetime": datetime.datetime(2025, 5, 12, 14, 30),
        "decimal": Decimal("12.50"),
    }
    encoded = JsonCoder.encode(value)
    decoded = JsonCoder.decode(encoded)

    assert decoded == {
        "date": {"val": "2025-05-12", "_spec_type": "date"},
        "datetime": {"val": "2025-05-12 14:30:00", "_spec_type": "datetime"},
        "decimal": {"val": "12.50", "_spec_type": "decimal"},
    }
    response = JSONResponse({"ok": True})
    assert JsonCoder.encode(response) == response.body


def test_pickle_coder_round_trip_and_base_coder_contract():
    value = {"items": [1, 2]}
    encoded = PickleCoder.encode(value)

    assert PickleCoder.decode(encoded) == value
    assert PickleCoder.decode_as_type(encoded, type_=dict) == value

    try:
        Coder.encode(value)
    except NotImplementedError:
        pass
    else:
        raise AssertionError("Base coder must remain abstract")

    try:
        Coder.decode(encoded)
    except NotImplementedError:
        pass
    else:
        raise AssertionError("Base coder must remain abstract")


def test_default_key_builder_includes_function_arguments():
    def endpoint(value):
        return value

    first = default_key_builder(
        endpoint, "api:v1", request=None, response=None, args=(1,), kwargs={}
    )
    same = default_key_builder(
        endpoint, "api:v1", request=None, response=None, args=(1,), kwargs={}
    )
    changed = default_key_builder(
        endpoint, "api:v1", request=None, response=None, args=(2,), kwargs={}
    )

    assert first.startswith("api:v1:")
    assert first == same
    assert first != changed


def test_cache_miss_then_hit_sets_status_and_etag():
    backend = MemoryBackend()
    FastAPICache.init(backend, prefix="test", expire=30)
    calls = []

    @fastapi_cache(namespace="items")
    def endpoint(value):
        calls.append(value)
        return {"value": value}

    async def run():
        first_response = Response()
        first = await endpoint(
            4, request=make_request(), response=first_response
        )
        second_response = Response()
        second = await endpoint(
            4, request=make_request(), response=second_response
        )
        return first, first_response, second, second_response

    first, first_response, second, second_response = asyncio.run(run())
    assert first == second == {"value": 4}
    assert calls == [4]
    assert first_response.headers["X-Cache"] == "MISS"
    assert second_response.headers["X-Cache"] == "HIT"
    assert first_response.headers["ETag"] == second_response.headers["ETag"]


def test_cache_control_bypasses_or_refreshes_cache():
    backend = MemoryBackend()
    FastAPICache.init(backend, prefix="test", expire=30)
    calls = []

    @fastapi_cache()
    async def endpoint():
        calls.append(1)
        return len(calls)

    async def run():
        await endpoint(request=make_request(method="POST"), response=Response())
        await endpoint(
            request=make_request(headers=[(b"cache-control", b"no-store")]),
            response=Response(),
        )
        await endpoint(request=make_request(), response=Response())
        await endpoint(
            request=make_request(headers=[(b"cache-control", b"no-cache")]),
            response=Response(),
        )

    asyncio.run(run())
    assert len(calls) == 4


def test_cache_handles_backend_failures_without_losing_result():
    backend = MemoryBackend()
    backend.get_error = RuntimeError("read failed")
    backend.set_error = RuntimeError("write failed")
    FastAPICache.init(backend, prefix="test", expire=30)

    @fastapi_cache()
    def endpoint():
        return "available"

    assert asyncio.run(endpoint(request=make_request(), response=Response())) == "available"
