"""
nodes.py — the three processing steps of the Vishwa agent pipeline.

Node 1 — identify_intent  : extract country name + requested fields (JSON)
Node 2 — invoke_tool       : call the REST Countries API (no LLM)
Node 3 — synthesise_answer : generate a natural-language answer

All LLM calls use the LangChain BaseChatModel returned by get_llm(),
so the nodes are completely decoupled from any specific provider SDK.
"""

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agent.state import AgentState
from agent.tools import fetch_country
from providers import get_llm

logger = logging.getLogger(__name__)


# ── Node 1 ────────────────────────────────────────────────────────────────────


async def identify_intent(state: AgentState) -> dict[str, Any]:
    """
    Use the LLM to extract:
      • country_name     — the country the user is asking about
      • requested_fields — the specific data points they want

    Uses ainvoke() (non-streaming) — we need the full JSON before parsing.
    """
    system_text = """\
You are an intent-extraction assistant. Given a user question about a country,
extract two things and return ONLY valid JSON (no markdown, no explanation):

{
  "country_name": "<the country name or null if unclear>",
  "requested_fields": ["<field1>", "<field2>", ...]
}

Valid fields: capital, population, currencies, languages, region, subregion, area, flag.
Return all fields if no specific fields are requested.
Set country_name to null and requested_fields to [] if no country is identifiable."""

    messages = [
        SystemMessage(content=system_text),
        HumanMessage(content=state["user_query"]),
    ]

    response = await get_llm().ainvoke(messages)
    raw = response.content.strip()

    # Strip markdown code fences if any model wraps JSON in them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
        country_name: str | None = parsed.get("country_name")
        requested_fields: list[str] = parsed.get("requested_fields", [])
    except json.JSONDecodeError:
        logger.warning("Intent node returned non-JSON: %s", raw)
        country_name = None
        requested_fields = []

    logger.info("Intent | country=%s | fields=%s", country_name, requested_fields)
    return {"country_name": country_name, "requested_fields": requested_fields}


# ── Node 2 ────────────────────────────────────────────────────────────────────


async def invoke_tool(state: AgentState) -> dict[str, Any]:
    """
    Call the REST Countries API. No LLM involved — pure HTTP.
    Short-circuits with an error if no country was identified in node 1.
    """
    country_name = state.get("country_name")

    if not country_name:
        return {
            "raw_country_data": None,
            "tool_error": (
                "I couldn't identify a country in your question. "
                "Please mention a specific country (e.g. 'What is the capital of France?')."
            ),
        }

    data, error = await fetch_country(country_name)
    logger.info(
        "Tool | country=%s | error=%s | keys=%s",
        country_name,
        error,
        list(data.keys()) if data else None,
    )
    return {"raw_country_data": data, "tool_error": error}


# ── Node 3 ────────────────────────────────────────────────────────────────────


async def synthesise_answer(state: AgentState) -> dict[str, Any]:
    """
    Convert raw API data (or a tool error) into a clear, factual answer.
    Uses ainvoke() — returns the complete answer string.
    """
    # Fast path: propagate tool errors without hitting the LLM
    if state.get("tool_error"):
        return {"answer": state["tool_error"]}

    data = state.get("raw_country_data")
    if not data:
        return {
            "answer": "I was unable to retrieve data for that country. Please try again."
        }

    fields = state.get("requested_fields") or []
    context = _build_context(data, fields)

    system_text = """\
You are a helpful geography assistant. Answer the user's question using ONLY
the provided country data. Be concise and factual. Do not invent information.
If a requested piece of information is missing from the data, say so clearly."""

    user_text = f"""\
User question: {state["user_query"]}

Country data:
{context}

Answer the question based solely on the data above."""

    messages = [
        SystemMessage(content=system_text),
        HumanMessage(content=user_text),
    ]

    response = await get_llm().ainvoke(messages)
    answer = response.content.strip()

    logger.info("Synthesis complete | chars=%d", len(answer))
    return {"answer": answer}


# ── helpers ───────────────────────────────────────────────────────────────────


def _build_context(data: dict[str, Any], fields: list[str]) -> str:
    """
    Flatten only the relevant fields from the REST Countries payload
    into a clean key-value string to keep the synthesis prompt small.
    """
    ALL_FIELDS = {
        "capital",
        "population",
        "currencies",
        "languages",
        "region",
        "subregion",
        "area",
        "flag",
    }

    target = set(fields) & ALL_FIELDS if fields else ALL_FIELDS

    lines: list[str] = []
    name_info = data.get("name", {})
    lines.append(
        f"Country: {name_info.get('common', 'Unknown')} ({name_info.get('official', '')})"
    )

    if not fields or "capital" in target:
        capitals = data.get("capital", [])
        lines.append(f"Capital: {', '.join(capitals) if capitals else 'N/A'}")

    if not fields or "population" in target:
        pop = data.get("population")
        lines.append(
            f"Population: {pop:,}"
            if isinstance(pop, int)
            else f"Population: {pop or 'N/A'}"
        )

    if not fields or "currencies" in target:
        currencies = data.get("currencies", {})
        curr_str = (
            ", ".join(
                f"{v.get('name', k)} ({v.get('symbol', '')})"
                for k, v in currencies.items()
            )
            if currencies
            else "N/A"
        )
        lines.append(f"Currencies: {curr_str}")

    if not fields or "languages" in target:
        languages = data.get("languages", {})
        lines.append(
            f"Languages: {', '.join(languages.values()) if languages else 'N/A'}"
        )

    if not fields or "region" in target:
        lines.append(
            f"Region: {data.get('region', 'N/A')} / {data.get('subregion', 'N/A')}"
        )

    if not fields or "area" in target:
        area = data.get("area")
        lines.append(f"Area: {area:,.0f} km²" if area else "Area: N/A")

    return "\n".join(lines)
