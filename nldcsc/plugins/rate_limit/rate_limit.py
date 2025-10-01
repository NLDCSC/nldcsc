import time
from uuid import uuid4
from nldcsc.plugins.redis_client.wrapper import RedisWrapper


class RateLimit:
    def __init__(self, max_attempts: int = 5, time_window: int = 300):
        self.cache = RedisWrapper().redis_client
        self.max_attempts = max_attempts
        self.time_window = time_window

    def get_key(self, id: int):
        return f"{self.__class__.__name__}:limits:{id}"

    def attempt(self, id: int):
        name = self.get_key(id)
        key = uuid4().hex

        self.cache.hset(name, key, int(time.time()))
        self.cache.hexpire(name, self.time_window, key)

    def clear(self, id: int):
        self.cache.unlink(self.get_key(id))

    def limited(self, id: int):
        return self.cache.hlen(self.get_key(id)) >= self.max_attempts
