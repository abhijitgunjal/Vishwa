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
    country_names: list[str]        # e.g. ["Germany", "India"] — always a list
    requested_fields: list[str]     # e.g. ["population"]

    # ── Tool result (node 2) ───────────────────────────────────────────────
    raw_country_data: list[dict[str, Any]]  # one dict per country, same order
    tool_error: Optional[str]               # non-None if any fetch failed

    # ── Final answer (node 3) ──────────────────────────────────────────────
    answer: Optional[str]
