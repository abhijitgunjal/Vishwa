"""
Application lifespan management.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

from app.providers.factory import get_llm
from app.config.settings import get_settings
from app.cache.config import get_cache, close_cache

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # === STARTUP ===
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Cache Backend: {settings.cache_backend}")
    logger.info(f"Cache TTL: {settings.cache_ttl}s")

    # Initialise LLM provider
    try:
        llm = get_llm()
        logger.info(
            "LLM initialised | provider=%s | llm=%s",
            settings.llm_provider,
            type(llm).__name__,
        )
    except Exception as exc:
        logger.critical("Failed to initialise LLM provider: %s", exc)
        raise

    # Initialise cache
    try:
        get_cache()
        logger.info("Cache initialised successfully")
    except Exception as exc:
        logger.error("Failed to initialise cache: %s", exc)
        raise

    logger.info("Application startup complete")
    yield

    # === SHUTDOWN ===
    logger.info("Initiating graceful shutdown...")

    try:
        await close_cache()
        logger.info("Cache closed successfully")
    except Exception as exc:
        logger.error("Error closing cache: %s", exc)

    logger.info("Shutdown complete")
