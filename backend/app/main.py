import logging
import os
import time

from mangum import Mangum
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from dotenv import load_dotenv

from .api.lifespan import lifespan
from .api.routes import router
from .api.limiter import limiter

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

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

# ── rate limiter ──────────────────────────────────────────────────────────────
app.state.limiter = limiter

# ── CORS ──────────────────────────────────────────────────────────────────────
_allowed_origins = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:4173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SlowAPIMiddleware)

# ── timing middleware ─────────────────────────────────────────────────────────
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Response-Time"] = f"{time.perf_counter() - start:.3f}s"
    return response

# ── exception handlers ────────────────────────────────────────────────────────
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(status_code=429, content={"detail": "Too many requests"})

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s", request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred."},
    )

# ── welcome ───────────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return {"app": "Vishwa", "message": "Visit /docs for the interactive API documentation."}

# ── mount all routes ──────────────────────────────────────────────────────────
app.include_router(router)

handler = Mangum(app)
