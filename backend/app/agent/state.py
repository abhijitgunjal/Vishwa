"""
AgentState defines the shared state that flows through every node in the graph.
Keeping it in one place makes it easy to reason about what data is available
at each step and avoids hidden coupling between nodes.
"""

from typing import Any, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict):
    # ── Input ──────────────────────────────────────────────────────────────
    user_query: str

    # ── Intent / field identification (node 1) ─────────────────────────────
    country_name: Optional[str]          # extracted country name
    requested_fields: list[str]          # e.g. ["population", "capital"]

    # ── Tool result (node 2) ───────────────────────────────────────────────
    raw_country_data: Optional[dict[str, Any]]  # raw payload from REST Countries
    tool_error: Optional[str]                   # non-None when the API call failed

    # ── Final answer (node 3) ──────────────────────────────────────────────
    answer: Optional[str]
