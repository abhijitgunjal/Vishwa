"""
Cache configuration and factory.
"""

from app.cache.backend import CacheBackend, InMemoryCache
from app.config.settings import get_settings
import logging

logger = logging.getLogger(__name__)

_cache_instance: CacheBackend | None = None


def get_cache() -> CacheBackend:
    """
    Get or create the cache backend instance (singleton).
    
    The backend is determined by CACHE_BACKEND environment variable:
    - "memory": InMemoryCache (default, good for dev/single instance)
    - "redis": RedisCache (production, distributed)
    """
    global _cache_instance
    
    if _cache_instance is not None:
        return _cache_instance
    
    settings = get_settings()
    
    if settings.cache_backend == "memory":
        _cache_instance = InMemoryCache(
            maxsize=settings.cache_max_size,
            ttl=settings.cache_ttl
        )
    else:
        logger.warning(
            f"Unknown cache backend '{settings.cache_backend}', "
            f"falling back to in-memory cache"
        )
        _cache_instance = InMemoryCache(
            maxsize=settings.cache_max_size,
            ttl=settings.cache_ttl
        )
    
    return _cache_instance


async def close_cache():
    """Close cache connections (call on shutdown)."""
    global _cache_instance
    if _cache_instance and hasattr(_cache_instance, 'close'):
        await _cache_instance.close()
    _cache_instance = None
