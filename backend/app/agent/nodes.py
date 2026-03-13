"""
nodes.py — the three processing steps of the Vishwa agent pipeline.

Node 1 — identify_intent  : extract country names (1 or more) + requested fields
Node 2 — invoke_tool       : fetch each country from REST Countries API concurrently
Node 3 — synthesise_answer : generate a natural-language answer from all fetched data

Supports multi-country queries such as:
    "Germany population vs India population"
    "Compare the currencies of Japan and South Korea"
    "What are the capitals of France, Spain and Italy?"
"""

import asyncio
from fastapi import HTTPException
import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.agent.tools import fetch_country
from app.providers.factory import get_llm
from app.agent.constants import ALL_FIELDS
from app.agent.prompts import Prompts

logger = logging.getLogger(__name__)


# ── Node 1 ────────────────────────────────────────────────────────────────────


async def identify_intent(state: AgentState) -> dict[str, Any]:
    """
    Use the LLM to extract:
      • country_names    — list of countries mentioned (1 or more)
      • requested_fields — the specific data points the user wants

    Returns a list even for single-country queries so the rest of the
    pipeline never has to branch on "is this one country or many".
    """

    messages = [
        SystemMessage(content=Prompts.INTENT_SYSTEM),
        HumanMessage(content=state["user_query"]),
    ]

    try:
        async with asyncio.timeout(30):  # 30 seconds max
            response = await get_llm().ainvoke(messages)
    except asyncio.TimeoutError:
        logger.error("LLM call timed out after 30s")
        raise HTTPException(status_code=504, detail="The agent timed out. Please try again.")

    raw = response.content.strip()

    # Strip markdown code fences if any model wraps JSON in them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
        country_names: list[str] = parsed.get("country_names") or []
        requested_fields: list[str] = parsed.get("requested_fields", [])

        # Defensive: if the model returned a plain string instead of a list
        if isinstance(country_names, str):
            country_names = [country_names] if country_names else []

    except json.JSONDecodeError:
        logger.warning("Intent node returned non-JSON: %s", raw)
        country_names = []
        requested_fields = []

    logger.info("Intent | countries=%s | fields=%s", country_names, requested_fields)
    return {"country_names": country_names, "requested_fields": requested_fields}


# ── Node 2 ────────────────────────────────────────────────────────────────────


async def invoke_tool(state: AgentState) -> dict[str, Any]:
    """
    Fetch all countries concurrently using asyncio.gather.

    - If no countries were identified, short-circuit with an error.
    - If some fetches succeed and some fail, include what we have and
      note the failures in tool_error so the synthesis node can report them.
    - All successful results are collected in order into raw_country_data.
    """
    country_names: list[str] = state.get("country_names") or []

    if not country_names:
        return {
            "raw_country_data": [],
            "tool_error": (
                "I couldn't identify any country in your question. "
                "Please mention at least one country (e.g. 'What is the capital of France?')."
            ),
        }

    # Fetch all countries concurrently — much faster than sequential for 2+ countries
    results = await asyncio.gather(
        *[fetch_country(name) for name in country_names],
        return_exceptions=False,
    )

    raw_country_data: list[dict[str, Any]] = []
    errors: list[str] = []

    for name, (data, error) in zip(country_names, results):
        if error:
            logger.warning("Tool | country=%s | error=%s", name, error)
            errors.append(f"{name}: {error}")
        else:
            logger.info("Tool | country=%s | keys=%s", name, list(data.keys()))
            raw_country_data.append(data)

    tool_error = "; ".join(errors) if errors else None

    return {
        "raw_country_data": raw_country_data,
        "tool_error": tool_error,
    }


# ── Node 3 ────────────────────────────────────────────────────────────────────


async def synthesise_answer(state: AgentState) -> dict[str, Any]:
    """
    Convert raw API data from one or more countries into a clear, factual answer.

    If some countries failed to fetch, the error is noted in the prompt so
    the LLM can acknowledge the gap rather than silently ignoring it.
    """
    raw_country_data: list[dict[str, Any]] = state.get("raw_country_data") or []
    tool_error = state.get("tool_error")

    # Hard fail only if we have nothing at all
    if not raw_country_data and tool_error:
        return {"answer": tool_error}

    if not raw_country_data:
        return {
            "answer": "I was unable to retrieve data for that country. Please try again."
        }

    # In synthesise_answer, before building context:
    fields = [f for f in (state.get("requested_fields") or []) if f in ALL_FIELDS]

    # Build one context block per country, clearly separated
    context_blocks = [_build_context(data, fields) for data in raw_country_data]
    context = "\n\n---\n\n".join(context_blocks)

    # If some fetches failed, tell the LLM so it can mention the gap
    partial_error_note = (
        f"\nNote: Some countries could not be retrieved — {tool_error}"
        if tool_error
        else ""
    )

    messages = [
        SystemMessage(content=Prompts.SYNTHESIS_ANSWER_SYSTEM),
        HumanMessage(content=Prompts.synthesis_answer_user_text(
            query=state["user_query"],
            context=context,
            partial_error_note=partial_error_note
        )),
    ]

    try:
        async with asyncio.timeout(30):  # 30 seconds max
            response = await get_llm().ainvoke(messages)
    except asyncio.TimeoutError:
        logger.error("LLM call timed out after 30s")
        raise HTTPException(status_code=504, detail="The agent timed out. Please try again.")
    answer = response.content.strip()

    logger.info("Synthesis complete | chars=%d", len(answer))
    return {"answer": answer}


# ── helpers ───────────────────────────────────────────────────────────────────


def _build_context(data: dict[str, Any], fields: list[str]) -> str:
    """
    Flatten only the relevant fields from a single REST Countries payload
    into a clean key-value string to keep the synthesis prompt small.
    """

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
