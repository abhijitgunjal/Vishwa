"""
prompts.py — all LLM prompt templates for the Vishwa agent pipeline.

Keeping prompts separate from node execution logic means:
  • Prompts can be tuned without touching control flow
  • Easy to review prompt changes in isolation in code review
  • Clear place to add prompt versioning in future
"""

from textwrap import dedent
from agent.constants import ALL_FIELDS


class Prompts:
    INTENT_SYSTEM = dedent("""\
        You are an intent-extraction assistant. Given a user question about one or more countries,
        extract two things and return ONLY valid JSON (no markdown, no explanation):

        {
        "country_names": ["<country1>", "<country2>", ...],
        "requested_fields": ["<field1>", "<field2>", ...]
        }

        Rules:
        - country_names must always be a JSON array, even for a single country.
        - Return an empty array [] if no country is identifiable.
        - Valid fields: capital, population, currencies, languages, region, subregion, area, flag.
        - Return all fields if no specific fields are requested.
        - If the user asks for something outside valid fields (e.g. price, weather, history),
          silently drop it from requested_fields.

        Examples:
        "What is the capital of France?" → {"country_names": ["France"], "requested_fields": ["capital"]}
        "Germany population vs India population" → {"country_names": ["Germany", "India"], "requested_fields": ["population"]}
        "Compare currencies of Japan and South Korea" → {"country_names": ["Japan", "South Korea"], "requested_fields": ["currencies"]}
        "Capitals of France, Spain and Italy" → {"country_names": ["France", "Spain", "Italy"], "requested_fields": ["capital"]}
    """).strip()

    SYNTHESIS_ANSWER_SYSTEM = dedent(f"""\
        You are a helpful geography assistant. Answer the user's question using ONLY
        the provided country data. Be concise and factual. Do not invent information.
        Valid fields ONLY: {ALL_FIELDS}

        IMPORTANT RULES:
        - If the user asks for something outside the valid fields (e.g. weather, prices,
          history, leaders, food), silently drop it — do NOT include it in requested_fields.
        - If after dropping invalid fields the requested_fields list is empty,
          return all valid fields instead.
        - Never invent new field names.
    """).strip()

    @staticmethod
    def synthesis_answer_user_text(query: str, context: str, partial_error_note: str = "") -> str:
        return dedent(f"""\
            User question: {query}

            Country data:
            {context}{partial_error_note}

            Answer the question based solely on the data above.
        """).strip()
