"""
main.py — Vishwa: Country Information AI Agent

FastAPI entry point. Exposes:
  GET  /          — welcome
  GET  /health    — liveness probe
  GET  /info      — active provider + model
  POST /query     — ask a question, get a JSON answer
"""

import asyncio
import logging
import os
import time
import uuid
from mangum import Mangum
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent import agent, AgentState
from cache.backend import CacheBackend
from cache.config import get_cache
from providers import get_llm
from schemas import QueryRequest, QueryResponse
from agent.tools import fetch_country
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from config.settings import get_settings
from api.lifespan import lifespan

from dotenv import load_dotenv

load_dotenv()

# ── logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

settings = get_settings()
logger = logging.getLogger(__name__)


# ── app ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Vishwa",
    description=(
        "Vishwa — Country Information AI Agent. "
        "Answers natural-language questions about countries using a "
        "three-step LangGraph pipeline (intent → tool → synthesis). "
        "Supports Groq, AWS Bedrock, and OpenRouter as LLM backends."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter

# ── CORS ──────────────────────────────────────────────────────────────────────
_allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:4173",
).split(",")

# middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SlowAPIMiddleware)


# ── middleware: request timing ────────────────────────────────────────────────
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Response-Time"] = f"{time.perf_counter() - start:.3f}s"
    return response


# ── routes ────────────────────────────────────────────────────────────────────
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(status_code=429, content={"detail": "Too many requests"})


@app.get("/", include_in_schema=False)
async def root():
    return {
        "app": "Vishwa",
        "message": "Visit /docs for the interactive API documentation.",
    }


@app.get("/health", tags=["ops"])
async def health():
    """Liveness probe for Railway / Render / load balancers."""
    return {"status": "ok"}


@app.get("/info", tags=["ops"])
async def info():
    """Returns the active LLM provider name and model class."""
    llm = get_llm()
    return {
        "app": "Vishwa",
        "provider": settings.llm_provider,
        "llm_class": type(llm).__name__,
        "version": "1.0.0",
    }


@app.post("/query", response_model=QueryResponse, tags=["agent"])
@limiter.limit("5/minute;50/hour;200/day")
async def query(
    request: Request, body: QueryRequest, cache: CacheBackend = Depends(get_cache)
):
    """
    Ask a natural-language question about any country.
    """
    request_id = uuid.uuid4().hex[:8]
    logger.info(f"[{request_id}] POST /query | question={body.question}")

    # Check cache
    cache_key = f"query:{cache.generate_key(body.question)}"
    cached = await cache.get(cache_key)
    if cached:
        logger.info(f"[{request_id}] Cache hit")
        return QueryResponse(**cached)

    initial_state: AgentState = {
        "user_query": body.question,
        "country_names": [],
        "requested_fields": [],
        "raw_country_data": [],
        "tool_error": None,
        "answer": None,
    }

    try:
        async with asyncio.timeout(30):
            final_state: AgentState = await agent.ainvoke(initial_state)
    except Exception as exc:
        logger.exception("Agent pipeline failed | question=%s", body.question)
        raise HTTPException(
            status_code=500,
            detail="The agent encountered an internal error.",
        ) from exc

    answer = (
        final_state.get("answer")
        or "I was unable to generate an answer. Please try again."
    )
    response = QueryResponse(
        answer=answer,
        countries=final_state.get("country_names", []),
        fields=final_state.get("requested_fields", []),
    )
    # Cache response
    await cache.set(cache_key, response.model_dump(), ttl=settings.cache_ttl)
    logger.info(f"[{request_id}] Response cached (TTL={settings.cache_ttl}s)")
    return response


# ── global error handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s", request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred."},
    )


@app.get("/cache/info", tags=["ops"])
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


@app.delete("/cache", tags=["admin"])
async def clear_cache(cache: CacheBackend = Depends(get_cache)):
    """Clear all cached responses (admin endpoint)."""
    await cache.clear()
    return {"message": "Cache cleared successfully"}


handler = Mangum(app)
