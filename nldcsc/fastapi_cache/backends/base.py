from abc import ABC, abstractmethod
from typing import Optional


class Backend(ABC):
    @abstractmethod
    async def get_with_ttl(self, key: str) -> tuple[int, Optional[bytes]]:
        raise NotImplementedError

    @abstractmethod
    async def get(self, key: str) -> Optional[bytes]:
        raise NotImplementedError

    @abstractmethod
    async def set(self, key: str, value: bytes, expire: Optional[int] = None) -> None:
        raise NotImplementedError

    @abstractmethod
    async def clear(
        self, namespace: Optional[str] = None, key: Optional[str] = None
    ) -> int:
        raise NotImplementedError
