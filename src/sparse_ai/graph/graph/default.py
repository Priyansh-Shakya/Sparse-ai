"""
Builds a Default Graph is user does not Create one
"""

from sparse_ai.graph.nodes.nodes import Node
from sparse_ai.graph.edges.edges import END
from sparse_ai.graph.graph.graph import Graph

def default_agent_graph() -> Graph:
    """
    Minimal default graph: llm_call and tool_exec alternate until the model
    responds with plain text instead of a tool call, then the run ends.

        llm_call -> tool_exec   (if the model requested a tool call)
        llm_call -> END          (if the model gave a final text answer)
        tool_exec -> llm_call    (always, single destination — plain edge)
    """
    async def route_after_llm(state) -> str:
        if state.tool_calls:
            return "tool_exec"
        return END

    g = Graph()
    g.graph_builder(
        nodes={
            "llm_call": Node.llm_call(),
            "tool_exec": Node.tool_exec(),
        },
        edges=[
            ("tool_exec", "llm_call"),   # single destination — plain edge, no router needed
        ],
        routers=[
            ("llm_call", route_after_llm),   # two possible destinations — needs a router
        ],
        entry_point="llm_call",
    )
    return g