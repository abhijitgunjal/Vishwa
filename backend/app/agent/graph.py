"""
graph.py — wires the three nodes into a LangGraph StateGraph.

Pipeline:
    identify_intent → invoke_tool → synthesise_answer → END
"""

from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import identify_intent, invoke_tool, synthesise_answer


def _build_graph():
    g = StateGraph(AgentState)

    g.add_node("identify_intent", identify_intent)
    g.add_node("invoke_tool", invoke_tool)
    g.add_node("synthesise_answer", synthesise_answer)

    g.set_entry_point("identify_intent")
    g.add_edge("identify_intent", "invoke_tool")
    g.add_edge("invoke_tool", "synthesise_answer")
    g.add_edge("synthesise_answer", END)

    return g.compile()


# Module-level singleton — compiled once, reused across all requests
agent = _build_graph()
