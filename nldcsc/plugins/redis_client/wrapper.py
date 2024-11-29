import os
from urllib.parse import urlparse

import redis

from nldcsc.generic.utils import getenv_dict


class RedisWrapper(object):
    def __init__(
        self, redis_url: str = None, auto_connect : bool = True, **kwargs
    ):
        self._redis_client = None
        self.kwargs = kwargs
        self.redis_url = (
            redis_url
            if redis_url is not None
            else os.getenv("REDIS_URL", "redis://redis:6379/")
        )

        self.redis_cache_db = int(os.getenv("REDIS_CACHE_DB", 0))
        self.redis_kwargs = getenv_dict("REDIS_KWARGS", None)

        if self.redis_kwargs is not None:
            self.kwargs.update(self.redis_kwargs)

        if auto_connect:
            self.connect()
        

    def connect(self):
        parsed_url = urlparse(self.redis_url)

        self._redis_client = redis.Redis(
            host=str(parsed_url.hostname),
            port=int(parsed_url.port),
            db=int(self.redis_cache_db),
            **self.kwargs,
        )

    def __repr__(self):
        return "<< RedisWrapper >>"

    @property
    def redis_client(self) -> redis.Redis:
        return self._redis_client

    @property
    def set(self):
        return self._redis_client.set

    @property
    def delete(self):
        return self._redis_client.delete

    @property
    def get(self):
        return self._redis_client.get
