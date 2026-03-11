"""
tests/test_agent.py — unit tests for the Vishwa agent pipeline.

All LLM calls are mocked via LangChain's AIMessage so tests run
without any real API keys or network access.

Run with:
    pytest tests/ -v
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import AIMessage

from app.agent.state import AgentState
from app.agent.nodes import identify_intent, invoke_tool, synthesise_answer, _build_context


# ── fixtures ──────────────────────────────────────────────────────────────────

def make_state(**overrides) -> AgentState:
    base: AgentState = {
        "user_query": "What is the capital of France?",
        "country_name": None,
        "requested_fields": [],
        "raw_country_data": None,
        "tool_error": None,
        "answer": None,
    }
    return {**base, **overrides}


FRANCE_DATA = {
    "name": {"common": "France", "official": "French Republic"},
    "capital": ["Paris"],
    "population": 67391582,
    "currencies": {"EUR": {"name": "Euro", "symbol": "€"}},
    "languages": {"fra": "French"},
    "region": "Europe",
    "subregion": "Western Europe",
    "area": 551695.0,
}

INTENT_JSON = json.dumps({
    "country_name": "France",
    "requested_fields": ["capital"],
})


def mock_llm(content: str = INTENT_JSON) -> MagicMock:
    """Return a mock LangChain chat model that returns a fixed AIMessage."""
    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=AIMessage(content=content))
    return llm


# ── Node 1 ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_identify_intent_happy_path():
    state = make_state()
    with patch("app.agent.nodes.get_llm", return_value=mock_llm()):
        result = await identify_intent(state)
    assert result["country_name"] == "France"
    assert result["requested_fields"] == ["capital"]


@pytest.mark.asyncio
async def test_identify_intent_strips_markdown_fences():
    content = "```json\n" + INTENT_JSON + "\n```"
    state = make_state()
    with patch("app.agent.nodes.get_llm", return_value=mock_llm(content)):
        result = await identify_intent(state)
    assert result["country_name"] == "France"


@pytest.mark.asyncio
async def test_identify_intent_bad_json_handled_gracefully():
    state = make_state(user_query="what is the thing?")
    with patch("app.agent.nodes.get_llm", return_value=mock_llm("not json")):
        result = await identify_intent(state)
    assert result["country_name"] is None
    assert result["requested_fields"] == []


# ── Node 2 ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invoke_tool_happy_path():
    state = make_state(country_name="France")
    with patch("app.agent.nodes.fetch_country", new_callable=AsyncMock, return_value=(FRANCE_DATA, None)):
        result = await invoke_tool(state)
    assert result["raw_country_data"] == FRANCE_DATA
    assert result["tool_error"] is None


@pytest.mark.asyncio
async def test_invoke_tool_no_country_identified():
    state = make_state(country_name=None)
    result = await invoke_tool(state)
    assert result["raw_country_data"] is None
    assert "identify a country" in result["tool_error"]


@pytest.mark.asyncio
async def test_invoke_tool_api_returns_error():
    state = make_state(country_name="Neverland")
    with patch("app.agent.nodes.fetch_country", new_callable=AsyncMock, return_value=(None, "Country not found")):
        result = await invoke_tool(state)
    assert result["tool_error"] == "Country not found"


# ── Node 3 ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_synthesise_answer_happy_path():
    state = make_state(
        country_name="France",
        requested_fields=["capital"],
        raw_country_data=FRANCE_DATA,
    )
    with patch("app.agent.nodes.get_llm", return_value=mock_llm("The capital of France is Paris.")):
        result = await synthesise_answer(state)
    assert result["answer"] == "The capital of France is Paris."


@pytest.mark.asyncio
async def test_synthesise_answer_propagates_tool_error():
    state = make_state(tool_error="Country not found.")
    result = await synthesise_answer(state)
    assert result["answer"] == "Country not found."


@pytest.mark.asyncio
async def test_synthesise_answer_no_data():
    state = make_state(raw_country_data=None, tool_error=None)
    result = await synthesise_answer(state)
    assert "unable to retrieve" in result["answer"]


# ── _build_context ────────────────────────────────────────────────────────────

def test_build_context_all_fields():
    context = _build_context(FRANCE_DATA, [])
    assert "France" in context
    assert "Paris" in context
    assert "67,391,582" in context
    assert "Euro" in context
    assert "French" in context


def test_build_context_filtered_fields():
    context = _build_context(FRANCE_DATA, ["capital"])
    assert "Paris" in context
    assert "67,391,582" not in context  # population excluded


def test_build_context_sparse_data_no_crash():
    sparse = {"name": {"common": "Nowhere", "official": "Nowhere State"}}
    context = _build_context(sparse, [])
    assert "Nowhere" in context
    assert "N/A" in context


# ── schemas ───────────────────────────────────────────────────────────────────

def test_query_request_valid():
    from app.schemas import QueryRequest
    req = QueryRequest(question="What is the capital of Japan?")
    assert req.question == "What is the capital of Japan?"


def test_query_request_too_short_raises():
    from app.schemas import QueryRequest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        QueryRequest(question="Hi")
