"""
Application lifespan management.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

from providers.factory import get_llm
from config.settings import get_settings
from cache.config import get_cache, close_cache

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.
    
    Startup:
    - Initialize cache backend
    - Load any other resources
    
    Shutdown:
    - Close cache connections
    - Cleanup resources
    """
    settings = get_settings()

    try:
        llm = get_llm()
        logger.info(
            "Vishwa starting up | provider=%s | llm=%s",
            settings.llm_provider,
            type(llm).__name__,
        )
    except Exception as exc:
        logger.critical("Failed to initialise LLM provider: %s", exc)
        raise
    yield
    logger.info("Vishwa shutting down")
    
    # === STARTUP ===
    logger.info("=" * 50)
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Environment: {'Development' if settings.debug else 'Production'}")
    logger.info(f"Cache Backend: {settings.cache_backend}")
    logger.info(f"Cache TTL: {settings.cache_ttl}s")
    
    # Initialize cache
    try:
        cache = get_cache()
        logger.info("✓ Cache initialized successfully")
    except Exception as e:
        logger.error(f"✗ Failed to initialize cache: {e}")
        raise
    
    # Add other startup tasks here
    # e.g., database connection, load ML models, etc.
    
    logger.info("=" * 50)
    logger.info("Application startup complete")
    
    yield
    
    # === SHUTDOWN ===
    logger.info("=" * 50)
    logger.info("Initiating graceful shutdown...")
    
    try:
        await close_cache()
        logger.info("✓ Cache closed successfully")
    except Exception as e:
        logger.error(f"✗ Error closing cache: {e}")
    

    logger.info("Shutdown complete")
    logger.info("=" * 50)
