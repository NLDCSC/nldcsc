from typing import Optional, Tuple, Union

from redis.asyncio.client import Redis
from redis.asyncio.cluster import RedisCluster

from nldcsc.fastapi_cache.backends.base import Backend


class RedisBackend(Backend):
    def __init__(self, redis: Union[Redis, RedisCluster]):
        self.redis = redis
        self.is_cluster: bool = isinstance(redis, RedisCluster)

    async def get_with_ttl(self, key: str) -> Tuple[int, Optional[bytes]]:
        async with self.redis.pipeline(transaction=not self.is_cluster) as pipe:
            return await pipe.ttl(key).get(key).execute()  # type: ignore[union-attr,no-any-return]

    async def get(self, key: str) -> Optional[bytes]:
        return await self.redis.get(key)  # type: ignore[union-attr]

    async def set(self, key: str, value: bytes, expire: Optional[int] = None) -> None:
        await self.redis.set(key, value, ex=expire)  # type: ignore[union-attr]

    async def clear(
        self, namespace: Optional[str] = None, key: Optional[str] = None
    ) -> int:
        if namespace:
            pipeline = self.redis.pipeline()
            for key in self.redis.scan_iter(f"{namespace}:*"):
                await pipeline.unlink(key)
            return await pipeline.execute()
        elif key:
            return await self.redis.unlink(key)  # type: ignore[union-attr]
        return 0
