from fastapi import APIRouter, Depends
from ...providers.factory import get_llm
from ...cache.backend import CacheBackend
from ...cache.config import get_cache
from ...agent.tools import fetch_country
from ...config.settings import get_settings

router = APIRouter(tags=["ops"])
settings = get_settings()


@router.get("/health")
async def health():
    """Liveness probe for Railway / Render / load balancers."""
    return {"status": "ok"}


@router.get("/info")
async def info():
    """Returns the active LLM provider name and model class."""
    llm = get_llm()
    return {
        "app": "Vishwa",
        "provider": settings.llm_provider,
        "llm_class": type(llm).__name__,
        "version": "1.0.0",
    }


@router.get("/cache/info")
async def cache_info():
    info = fetch_country.cache_info()
    return {
        "hits": info.hits,
        "misses": info.misses,
        "current_size": info.currsize,
        "max_size": info.maxsize,
        "hit_rate": round(info.hits / (info.hits + info.misses) * 100, 1)
        if (info.hits + info.misses) > 0
        else 0,
    }


@router.delete("/cache", tags=["admin"])
async def clear_cache(cache: CacheBackend = Depends(get_cache)):
    """Clear all cached responses (admin endpoint)."""
    await cache.clear()
    return {"message": "Cache cleared successfully"}
