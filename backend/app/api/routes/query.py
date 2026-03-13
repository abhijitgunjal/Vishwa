import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from ...agent import agent, AgentState
from ...cache.backend import CacheBackend
from ...cache.config import get_cache
from ...config.settings import get_settings
from ...schemas import QueryRequest, QueryResponse
from ..limiter import limiter

router = APIRouter(tags=["agent"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/query", response_model=QueryResponse)
@limiter.limit("5/minute;50/hour;200/day")
async def query(
    request: Request,
    body: QueryRequest,
    cache: CacheBackend = Depends(get_cache),
):
    request_id = uuid.uuid4().hex[:8]
    logger.info("[%s] POST /query | question=%s", request_id, body.question)

    # Check cache
    cache_key = f"query:{cache.generate_key(body.question)}"
    cached = await cache.get(cache_key)
    if cached:
        logger.info("[%s] Cache hit", request_id)
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
    except asyncio.TimeoutError:
        logger.error("[%s] Agent timed out", request_id)
        raise HTTPException(status_code=504, detail="The agent timed out. Please try again.")
    except Exception as exc:
        logger.exception("[%s] Agent pipeline failed", request_id)
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

    await cache.set(cache_key, response.model_dump(), ttl=settings.cache_ttl)
    logger.info("[%s] Response cached (TTL=%ss)", request_id, settings.cache_ttl)
    return response
