"""
Responsible for EDGES Blah Blah
"""

# A conditional Edge is represented as:
# conditional_edge: lambda state: 'node_x' if state.state_value else 'node_y'





import inspect
from typing import Callable, Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sparse_ai.graph.graph.graph import Graph


START = "START"
END = "END"

class Edge:
    """
    Defines a connection between nodes in a graph.

    An edge can either connect one node directly to another, or use a
    conditional router to determine the next node based on the current state.

    For a direct edge, provide `start` and `end`:

        Edge("process", "llm")

    For a conditional edge, provide `start`, `conditional_edge`, and a
    `path_map`. The router returns a label, which is mapped to the
    corresponding target node through `path_map`:

        Edge(
            "llm",
            conditional_edge=router,
            path_map={
                "has_tools": "tools",
                "done": END,
            },
        )

    Args:
        start (str): Name of the node where the edge originates.
        end (str | None): Name of the node to connect to for a direct edge.
            Cannot be used together with `conditional_edge`.
        conditional_edge (callable | None): A function that receives the
            current graph state and returns a routing label. The returned
            label must exist in `path_map`.
        path_map (dict[str, str] | None): Maps router outcomes to target
            node names. Required when using a conditional edge.

    Raises:
        ValueError: If neither `end` nor `conditional_edge` is provided.
        ValueError: If both `end` and `conditional_edge` are provided.
        ValueError: If a conditional edge does not provide a `path_map`.

    Example:
        Direct edge:

            Edge("start", "llm")

        Conditional edge:

            Edge(
                "llm",
                conditional_edge=Node.default_router(),
                path_map={
                    "has_tools": "tools",
                    "done": END,
                },
            )
    """
    def __init__(self, start: str, end: Optional[str] = None, router: Optional[Callable] = None,  display_paths: dict | None = None):
        if end is not None and router is not None:
            raise ValueError(f"Edge from '{start}' cannot have both 'end' and 'router' — pick one.")
        if end is None and router is None:
            raise ValueError(f"Edge from '{start}' needs either 'end' or 'router'.")
        self.start = start
        self.end = end
        self.router = router
        self.display_paths = display_paths

    async def resolve(self, state, graph: "Graph") -> str:
        """
        Returns the real next-node name.
        For a static edge, this is just `end`.
        For a router edge, this calls the router (awaiting it if it's async),
        then validates the returned name actually exists in the graph before
        trusting it — this is the ValueError guard replacing path_map.
        """
        if self.router is None:
            return self.end

        result = self.router(state)
        if inspect.isawaitable(result):        # supports both sync and async router functions
            result = await result

        if not isinstance(result, str):
            raise TypeError(
                f"Router for node '{self.start}' must return a string (a node name or END), "
                f"got {type(result).__name__}."
            )

        graph._check_ref(result)   # raises ValueError if `result` isn't a real node name or END
        return result
    
    @classmethod
    def tool_router(cls, start: str, tool_node: str):
        def _check(state):
            return tool_node if state.tool_calls else cls.END
        return cls(start=start, conditional_edge=_check)


    @staticmethod
    def to_dict_list(edges:list):
        """Convert a collection of edges into a serializable edge representation."""
        return [{i.start:i.end} for i in edges]

    