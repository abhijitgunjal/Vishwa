"""
providers — LangChain-based pluggable LLM backends for Vishwa.

Supported providers (set via LLM_PROVIDER env var):
    groq        → ChatGroq
    bedrock     → ChatBedrock
    openrouter  → ChatOpenAI pointed at openrouter.ai

Public API:
    from app.providers import get_llm
"""

from .factory import get_llm

__all__ = ["get_llm"]
