import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from redis import Redis
from redis.asyncio import Redis as AsyncRedis

import nldcsc.redis_cache as redis_cache_module
from nldcsc.redis_cache import (
    RedisCache,
    async_chunks,
    chunks,
    compact_dump,
    get_args,
)


def test_compact_dump_and_argument_normalization():
    def endpoint(first, second=2, *extra, flag=True, **options):
        return None

    assert compact_dump({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    assert get_args(endpoint, (1, 3, 4), {"flag": False, "custom": "value"}) == {
        "first": 1,
        "second": 3,
        "extra": [4],
        "flag": False,
        "options": {"custom": "value"},
    }


def test_chunks_split_iterables_into_requested_sizes():
    assert list(chunks(range(5), 2)) == [[0, 1], [2, 3], [4]]
    assert list(chunks([], 3)) == []


def test_async_chunks_split_async_iterables():
    async def values():
        for value in range(5):
            yield value

    async def run():
        return [part async for part in async_chunks(values(), 2)]

    assert asyncio.run(run()) == [[0, 1], [2, 3], [4]]


def test_sync_cache_decorator_uses_cached_value_and_can_bypass(monkeypatch):
    client = Redis()
    client.get = Mock(return_value=None)
    pipeline = Mock()
    client.pipeline = Mock(return_value=pipeline)
    script = Mock()
    monkeypatch.setattr(redis_cache_module, "get_cache_lua_fn", Mock(return_value=script))
    cache = RedisCache(client).cache(ttl=20, namespace="items")
    calls = []

    @cache
    def calculate(value):
        calls.append(value)
        return value * 2

    assert calculate(3) == 6
    script.assert_called_once()
    client.get.return_value = b"8"
    assert calculate(4) == 8
    assert calls == [3]
    assert calculate.invalidate(3) is None
    pipeline.delete.assert_called_once()
    pipeline.zrem.assert_called_once()
    pipeline.execute.assert_called_once()

    bypass = RedisCache(client, active=False).cache()

    @bypass
    def uncached(value):
        return value

    assert uncached(5) == 5


def test_sync_cache_decorator_calls_exception_handler(monkeypatch):
    client = Redis()
    client.get = Mock(side_effect=RuntimeError("redis down"))
    handler = Mock(return_value="fallback")
    cache = RedisCache(client, exception_handler=handler).cache()

    @cache
    def calculate(value):
        return value * 2

    assert calculate(3) == "fallback"
    handler.assert_called_once()


def test_async_cache_decorator_supports_async_function(monkeypatch):
    client = AsyncRedis()
    client.get = AsyncMock(return_value=None)
    script = AsyncMock()
    monkeypatch.setattr(redis_cache_module, "get_cache_lua_fn", Mock(return_value=script))
    cache = RedisCache(client).cache(ttl=5)

    @cache
    async def calculate(value):
        return value + 1

    async def run():
        return await calculate(2)

    assert asyncio.run(run()) == 3
    script.assert_awaited_once()


def test_cache_methods_enforce_client_mode(monkeypatch):
    sync_client = Redis()
    sync_client.set = Mock(return_value=True)
    sync_client.get = Mock(return_value=b"value")
    cache = RedisCache(sync_client)

    assert cache.set("key", "value") is True
    assert cache.get("key") == b"value"
    with pytest.raises(RuntimeError, match="async Redis client"):
        asyncio.run(cache.async_set("key", "value"))

    async_client = AsyncRedis()
    async_client.set = AsyncMock(return_value=True)
    async_client.get = AsyncMock(return_value=b"value")
    async_cache = RedisCache(async_client)

    assert asyncio.run(async_cache.async_set("key", "value")) is True
    assert asyncio.run(async_cache.async_get("key")) == b"value"
    with pytest.raises(RuntimeError, match="synchronous Redis client"):
        async_cache.get("key")
