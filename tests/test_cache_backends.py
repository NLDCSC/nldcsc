import asyncio
from unittest.mock import AsyncMock, Mock

from nldcsc.fastapi_cache.backends.redis import RedisBackend


class Pipeline:
    def __init__(self, result=None):
        self.result = result
        self.ttl = Mock(return_value=self)
        self.get = Mock(return_value=self)
        self.unlink = AsyncMock()
        self.execute = AsyncMock(return_value=result)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


class AsyncRedisStub:
    def __init__(self):
        self.pipeline_result = Pipeline((5, b"value"))
        self.pipeline = Mock(return_value=self.pipeline_result)
        self.get = AsyncMock(return_value=b"value")
        self.set = AsyncMock(return_value=True)
        self.unlink = AsyncMock(return_value=1)
        self.scan_iter = Mock(return_value=iter(["cache:a", "cache:b"]))


def test_redis_backend_get_set_and_ttl_pipeline():
    redis = AsyncRedisStub()
    backend = RedisBackend(redis)

    async def run():
        ttl_value = await backend.get_with_ttl("cache:key")
        value = await backend.get("cache:key")
        await backend.set("cache:key", b"new", expire=20)
        return ttl_value, value

    assert asyncio.run(run()) == ((5, b"value"), b"value")
    redis.pipeline.assert_called_once_with(transaction=True)
    redis.pipeline_result.ttl.assert_called_once_with("cache:key")
    redis.pipeline_result.get.assert_called_once_with("cache:key")
    redis.set.assert_awaited_once_with("cache:key", b"new", ex=20)


def test_redis_backend_clear_by_namespace_or_key():
    redis = AsyncRedisStub()
    redis.pipeline_result.execute.return_value = [1, 1]
    backend = RedisBackend(redis)

    async def run():
        by_namespace = await backend.clear(namespace="cache")
        by_key = await backend.clear(key="cache:a")
        no_filter = await backend.clear()
        return by_namespace, by_key, no_filter

    assert asyncio.run(run()) == ([1, 1], 1, 0)
    assert redis.pipeline_result.unlink.await_count == 2
    redis.unlink.assert_awaited_once_with("cache:a")
