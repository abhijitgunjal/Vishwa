"""
providers/factory.py — builds a LangChain BaseChatModel from env vars.

LLM_PROVIDER controls which backend is used:

    groq        → langchain_groq.ChatGroq
                  Requires: GROQ_API_KEY
                  Optional: GROQ_MODEL (default: llama-3.3-70b-versatile)

    bedrock     → langchain_aws.ChatBedrock
                  Requires: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
                  Optional: BEDROCK_MODEL (default: amazon.nova-lite-v1:0)

    openrouter  → langchain_openai.ChatOpenAI (pointed at openrouter.ai)
                  Requires: OPENROUTER_API_KEY
                  Optional: OPENROUTER_MODEL (default: meta-llama/llama-3.3-70b-instruct)

All three return a standard LangChain BaseChatModel, so nodes.py never
needs to know which provider is active.
"""

import logging
import os

from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)

# Singleton — built once at startup, reused across all requests
_llm_instance: BaseChatModel | None = None


def get_llm() -> BaseChatModel:
    """Return the singleton LangChain chat model for the configured provider."""
    global _llm_instance  # noqa: PLW0603
    if _llm_instance is None:
        _llm_instance = _build_llm()
    return _llm_instance


def _build_llm() -> BaseChatModel:
    provider = os.getenv("LLM_PROVIDER", "groq").lower().strip()

    if provider == "groq":
        return _build_groq()
    elif provider == "bedrock":
        return _build_bedrock()
    elif provider == "openrouter":
        return _build_openrouter()
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER='{provider}'. "
            "Valid values: groq | bedrock | openrouter"
        )


def _build_groq() -> BaseChatModel:
    try:
        from langchain_groq import ChatGroq  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "langchain-groq is required. Install with: pip install langchain-groq"
        ) from exc

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    logger.info("LLM provider: Groq | model=%s", model)
    return ChatGroq(model=model)  # reads GROQ_API_KEY from env


def _build_bedrock() -> BaseChatModel:
    try:
        from langchain_aws import ChatBedrock  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "langchain-aws is required. Install with: pip install langchain-aws"
        ) from exc

    model = os.getenv("BEDROCK_MODEL", "amazon.nova-lite-v1:0")
    region = os.getenv("AWS_REGION", "us-east-1")
    logger.info("LLM provider: Bedrock | model=%s | region=%s", model, region)
    return ChatBedrock(
        model_id=model,
        region_name=region,
        # AWS credentials are read from env:
        # AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY (or IAM role)
    )


def _build_openrouter() -> BaseChatModel:
    try:
        from langchain_openai import ChatOpenAI  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "langchain-openai is required. Install with: pip install langchain-openai"
        ) from exc

    model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")
    api_key = os.environ["OPENROUTER_API_KEY"]

    extra_headers: dict[str, str] = {}
    if site_url := os.getenv("OPENROUTER_SITE_URL"):
        extra_headers["HTTP-Referer"] = site_url
    if app_name := os.getenv("OPENROUTER_APP_NAME", "Vishwa"):
        extra_headers["X-Title"] = app_name

    logger.info("LLM provider: OpenRouter | model=%s", model)
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers=extra_headers or None,
    )
