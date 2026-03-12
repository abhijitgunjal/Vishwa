"""
Cache backend implementations with a unified interface.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
import json
import hashlib
from cachetools import TTLCache
import logging

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[dict]:
        """Retrieve value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: dict, ttl: int) -> None:
        """Store value in cache with TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove value from cache."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass

    @staticmethod
    def generate_key(raw_key: str) -> str:
        """Generate a stable hash key."""
        return hashlib.md5(raw_key.lower().strip().encode()).hexdigest()


class InMemoryCache(CacheBackend):
    """In-memory TTL cache using cachetools."""
    
    def __init__(self, maxsize: int = 1000, ttl: int = 3600):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.ttl = ttl
        logger.info(f"Initialized InMemoryCache (maxsize={maxsize}, ttl={ttl}s)")

    async def get(self, key: str) -> Optional[dict]:
        return self.cache.get(key)

    async def set(self, key: str, value: dict, ttl: int) -> None:
        # Note: cachetools TTLCache uses global TTL, can't set per-key
        self.cache[key] = value

    async def delete(self, key: str) -> None:
        self.cache.pop(key, None)

    async def clear(self) -> None:
        self.cache.clear()
