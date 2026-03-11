"""
main.py — Vishwa: Country Information AI Agent

FastAPI entry point. Exposes:
  GET  /          — welcome
  GET  /health    — liveness probe
  GET  /info      — active provider + model
  POST /query     — ask a question, get a JSON answer
"""

import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent import agent, AgentState
from providers import get_llm
from schemas import QueryRequest, QueryResponse

from dotenv import load_dotenv
load_dotenv()

# ── logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ── lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        llm = get_llm()
        logger.info(
            "Vishwa starting up | provider=%s | llm=%s",
            os.getenv("LLM_PROVIDER", "groq"),
            type(llm).__name__,
        )
    except Exception as exc:
        logger.critical("Failed to initialise LLM provider: %s", exc)
        raise
    yield
    logger.info("Vishwa shutting down")


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

# ── CORS ──────────────────────────────────────────────────────────────────────
_allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:4173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── middleware: request timing ────────────────────────────────────────────────
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Response-Time"] = f"{time.perf_counter() - start:.3f}s"
    return response


# ── routes ────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return {"app": "Vishwa", "message": "Visit /docs for the interactive API documentation."}


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
        "provider": os.getenv("LLM_PROVIDER", "groq"),
        "llm_class": type(llm).__name__,
        "version": "1.0.0",
    }


@app.post("/query", response_model=QueryResponse, tags=["agent"])
async def query(request: QueryRequest):
    """
    Ask a natural-language question about any country.

    **Examples**
    - `"What is the population of Germany?"`
    - `"What currency does Japan use?"`
    - `"What is the capital and population of Brazil?"`
    """
    logger.info("POST /query | question=%s", request.question)

    initial_state: AgentState = {
        "user_query": request.question,
        "country_name": None,
        "requested_fields": [],
        "raw_country_data": None,
        "tool_error": None,
        "answer": None,
    }

    try:
        final_state: AgentState = await agent.ainvoke(initial_state)
    except Exception as exc:
        logger.exception("Agent pipeline failed | question=%s", request.question)
        raise HTTPException(
            status_code=500,
            detail="The agent encountered an internal error.",
        ) from exc

    answer = final_state.get("answer") or "I was unable to generate an answer. Please try again."
    return QueryResponse(
        answer=answer,
        country=final_state.get("country_name"),
        fields=final_state.get("requested_fields", []),
    )


# ── global error handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s", request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred."},
    )
