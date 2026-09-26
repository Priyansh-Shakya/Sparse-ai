"""
Creates a Graph
"""



from typing import Callable, Optional

from sparse_ai.graph.nodes.special_nodes import ApprovalConfig, approval_node

from sparse_ai.state.state import State
from sparse_ai.graph.nodes.nodes import Node
from sparse_ai.tools.tool_result import ToolResult, ToolResultFormatter
from sparse_ai.graph.graph.display import GraphDisplay
from sparse_ai.graph.edges.edges import START, Edge , END
from sparse_ai.messages.messages import Message


import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)




from typing import Callable


class Graph:
    """
    Represents a directed execution graph for an agent.

    A graph consists of named nodes and edges that define the order in which
    those nodes are executed. Nodes perform work on the shared graph state,
    while edges determine which node is executed next. Edges may be static or
    conditional, with routers allowing the next node to be selected at runtime.

    Graphs are normally constructed using `graph_builder()`, which is the
    primary interface for defining nodes, edges, routers, and the graph's
    entry point. Once configured, the graph can be compiled and executed by
    an `Agent`.

    The graph can also be inspected through its representation and
    `to_dict()` methods, or visualized using `display_graph()`.

    A graph should not be modified after it has been compiled.

    Attributes:
        nodes (dict[str, Callable]):
            Registered node names mapped to their callable implementations.
        edges (list[Edge]):
            Edges defining the graph's execution flow.
        _entry_point (Optional[str]):
            Node at which graph execution begins.
        _compiled (bool):
            Whether the graph has been compiled and is ready for execution.

    Methods:
        graph_builder(...):
            Define and validate the graph's nodes, edges, routers, and entry
            point.
        run(...):
            Execute the graph starting from its configured entry point.
        display_graph(...):
            Render the graph as a visual diagram.
        to_dict():
            Return a serializable representation of the graph structure.

    Example:
        >>> graph = Graph().graph_builder(
        ...     nodes={
        ...         "chat": Node.llm_call(),
        ...         "tool": Node.tool_exec(),
        ...     },
        ...     edges=[
        ...         (START, "chat"),
        ...         ("chat", "tool"),
        ...     ],
        ... )
        >>>
        >>> graph.display_graph()
    """
    def __init__(self):
        self.nodes: dict[str, Callable] = {}
        self.edges: list[Edge] = []
        self._entry_point: Optional[str] = None
        self._compiled = False

    # ============================================================
    # REGISTRATION
    # ============================================================

    def _add_node(self, name: str, func):
        """
    Internal graph-building method.

    Register a node in the graph. This method is intended to be used
    internally by the graph-building API and is not meant to be called
    directly by users.

    Each node is identified by a unique name and is associated with a
    callable that is executed when the graph reaches that node.

    Node names cannot be `START` or `END`, as these names are reserved
    by the framework.

    Args:
        name (str): Unique name identifying the node.
        func (Callable): Callable associated with the node.

    Raises:
        ValueError: If `name` is `START` or `END`.
        ValueError: If a node with the same name is already registered.
    """
        if name in (START, END):
            raise ValueError(
                f"'{name}' is reserved and can't be used as a node name"
            )

        if name in self.nodes:
            raise ValueError(
                f"Node '{name}' is already registered"
            )

        self.nodes[name] = func

    def _add_edge(self, start: str, end: Optional[str] = None, router: Optional[Callable] = None, display_paths =None):
        """
        Internal graph-building method.

        Register an edge between graph nodes. For conditional edges, `router`
        determines the destination at runtime, so its destination is not
        validated during graph construction.
        """

        if start == END:
            raise ValueError("END cannot be a start — nothing can execute after the graph ends.")
        
        self._check_ref(start)
        if router is None:
            self._check_ref(end)
            
        self.edges.append(Edge(start=start, end=end, router=router, display_paths=display_paths))

        

    def set_entry_point(self, name: str):
        self._check_ref(name)
        self._entry_point = name

    def graph_builder(
        self,
        nodes: dict[str, Callable],
        edges: Optional[list[tuple[str, str]]] = None,
        routers: Optional[list[tuple]] = None,   # (start, router_fn) — one router per branching node
        entry_point: Optional[str] = None,
    ):
        
        """
        One call to fully define a graph's shape. This is the primary way
        users are expected to build a graph.

        Args:
            nodes (dict[str, Callable]):
                Mapping of node names to node functions.
                    {
                        "chat": Node.llm_call(),        # framework-resolved at compile()
                        "tool": Node.tool_exec(),       # framework-resolved at compile()
                        "validate": my_validate_fn,     # a plain user-defined function
                        "approval": Node.approval_node( # auto-generates its own router
                            on_approved="tool",
                            on_rejected="chat",
                        ),
                    }

            edges (list[tuple[str, str]], optional):
                Static, single-destination connections — use these ONLY when a node
                has exactly one possible next node. A node cannot appear as the
                start of both an `edges` entry and a `routers` entry — pick one.
                    [
                        (START, "chat"),      # (START, x) sets x as the entry point — not a real edge
                        ("validate", "tool"),
                    ]

            routers (list[tuple], optional):
                One entry per node that has MORE than one possible next node.
                Each entry is (start, router_fn) or (start, router_fn, display_paths):

                    start (str):
                        The branching node's name.

                    router_fn (Callable[[State], str]):
                        Sync or async. Receives the current `state` and MUST return
                        the REAL NAME of the next node (or END) — not a label that
                        gets translated, the actual node name itself. A bad return
                        value raises ValueError at run time, when that branch is
                        actually taken (not at build time — the router's real
                        behavior can't be known without running it).

                    display_paths (dict[str, str], optional — 3rd tuple item):
                        Display-only hint for `display_graph()`, listing the
                        branches this router can take, e.g. {"has_tool": "tool",
                        "done": END}. Never affects execution or validation —
                        purely cosmetic, so the diagram can draw real arrows out
                        of this node instead of leaving it unlabeled. Safe to
                        omit; the node still renders, just without drawn branches.

                    Example:
                        [
                            (
                                "chat",
                                route_after_chat,
                                {"has_tool": "tool", "done": END},   # optional, for the diagram only
                            ),
                        ]

            entry_point (str, optional):
                Explicit node to use as the graph's entry point. Takes precedence
                over both the auto-inferred entry point and a (START, x) edge.

        Returns:
            Graph: The configured and validated graph instance.

        Raises:
            ValueError: If a node/edge/router references an unknown node, if a
                node has multiple static edges, multiple routers, or both a
                static edge and a router, or if any node is unreachable (only
                checked when the graph has no routers at all — see `validate`).

        Example:
            >>> async def route_after_chat(state) -> str:
            ...     if state.tool_calls:
            ...         return "tool"
            ...     return END
            ...
            >>> graph = Graph().graph_builder(
            ...     nodes={
            ...         "chat": Node.llm_call(),
            ...         "tool": Node.tool_exec(),
            ...         "validate": my_validate_fn,
            ...         "approval": Node.approval_node(on_approved="tool", on_rejected="chat"),
            ...     },
            ...     edges=[
            ...         (START, "chat"),
            ...         ("validate", "tool"),
            ...     ],
            ...     routers=[
            ...         ("chat", route_after_chat, {"has_tool": "tool", "done": END}),
            ...     ],
            ...     entry_point="chat",
            ... )
        """
        # 1. Register every node first, so edges/routers below can validate against them.
        for name, func in nodes.items():
            self._add_node(name, func)

            # Approval nodes auto-generate their own router — this is a binary decision
            # by definition (approve/reject), so there's nothing for the user to write here.
            # on_approved/on_rejected are real node names already, so the router just
            # returns one of them directly — no path_map translation needed.
            # in graph_builder, when adding the auto-generated approval router:
            if isinstance(func, ApprovalConfig):
                def _approval_router(state, _cfg=func):
                    return _cfg.on_approved if state.approval_result == "approve" else _cfg.on_rejected
                self._add_edge(name, router=_approval_router,
                            display_paths={"approve": func.on_approved, "reject": func.on_rejected})

        # 2. Static edges — plain, single-destination connections.
        for start, end in (edges or []):
            if start == START:
                self.set_entry_point(end)   # (START, 'chat') means "chat is the entry point" — not a real edge
                continue
            if end == START:
                raise ValueError(f"START cannot be a destination — got edge ({start}, {end}).")
            self._add_edge(start, end)

        # 3. Routers — one per branching node, returns a real node name at runtime.
        #    Optional 3rd tuple item: display-only hint of possible outcomes, for the diagram.
        for entry in (routers or []):
            start, router_fn = entry[0], entry[1]
            display_paths = entry[2] if len(entry) > 2 else None
            self._add_edge(start, router=router_fn, display_paths=display_paths)

        # 4. Entry point — explicit call always wins over the auto-inferred one.
        if entry_point:
            self.set_entry_point(entry_point)

        Graph.validate(self)
        return self

    def _check_ref(self, name: str):
        """Raises ValueError unless `name` is a real registered node or END."""
        if name != END and name not in self.nodes:
            raise ValueError(f"Unknown node '{name}' — register it via graph_builder(nodes=...) first.")

    
    @staticmethod
    def validate(self):
        """
        Build-time sanity checks, run once at the end of graph_builder():

        1. Entry point: the graph MUST have one, set either via a (START, node)
        edge or an explicit entry_point= argument. Without this, Graph.run()
        has no way to know where to begin.
        2. Ambiguous branching: a node with more than one STATIC edge (no router)
        is a mistake — the graph can't know which one to take.
        3. Multiple routers on one node: only one router per branching node is allowed.
        4. Both static edge and router on one node: pick one, not both.
        5. Unreachable nodes: checked ONLY when the graph has no routers at all.
        Once any router exists, we can't reliably tell which nodes it can reach
        without running it against real state — so we trust the user and let a
        genuine mistake surface at runtime instead (as "no edge from node X").
        """
        from collections import Counter

        if self._entry_point is None:
            raise ValueError(
                "Graph has no entry point. Add a (START, 'node_name') edge, "
                "or pass entry_point='node_name' to graph_builder()."
            )

        static_starts = [e.start for e in self.edges if e.router is None]
        ambiguous = {name for name, count in Counter(static_starts).items() if count > 1}
        if ambiguous:
            raise ValueError(f"Node(s) {ambiguous} have multiple static edges — ambiguous.")

        router_starts = [e.start for e in self.edges if e.router is not None]
        multi_router = {name for name, count in Counter(router_starts).items() if count > 1}
        if multi_router:
            raise ValueError(f"Node(s) {multi_router} have more than one router — only one allowed.")

        both = set(static_starts) & set(router_starts)
        if both:
            raise ValueError(f"Node(s) {both} have BOTH a static edge and a router — pick one.")

        has_any_router = len(router_starts) > 0
        if not has_any_router:
            reachable_via_static_edges = {e.end for e in self.edges if e.end is not None}
            unreachable = set(self.nodes) - {self._entry_point} - reachable_via_static_edges
            if unreachable:
                raise ValueError(
                    f"Unreachable node(s): {unreachable}. Add an edge pointing to them, "
                    f"or remove them from `nodes` if unused."
                )
            
    # ---------------------------------------------------------------
    # COMPILE — resolves special node markers into real functions,
    # using the client/tools that only exist once an Agent is built.
    # ---------------------------------------------------------------

    def compile(self, client, tools=None):
        tools = tools or []
        for name, func in list(self.nodes.items()):
            if func == Node._LLM_CALL:
                self.nodes[name] = self._build_llm_node(client, tools)
            elif func == Node._TOOL_EXEC:
                self.nodes[name] = self._build_tool_node(client, tools)
            elif isinstance(func, ApprovalConfig):
                self.nodes[name] = self._build_approval_node(client, func)
        self._compiled = True
        return self

    # ============================================================
    # LLM NODE
    # ============================================================

    def _build_llm_node(self, client, tools):

        async def llm_call(state: State) -> State:

            response = await client.adapter.generate(
                messages=Message.serialize(
                    state.messages
                ),
                tools=tools,
            )

            state.last_response = response

            # Store tool calls in state.
            #
            # IMPORTANT:
            # This node does NOT decide where to go next.
            #
            # The graph author decides whether tool_calls should
            # lead to a tool node, another LLM node, approval,
            # END, etc.
            state.tool_calls = response.tool_calls

            # Preserve message handling.
            if response.tool_calls:

                state.messages.append(
                    Message.from_dict(
                        client.adapter.format_assistant_turn(
                            response.raw
                        )
                    )
                )

            else:

                state.messages.append(
                    Message.assistant(
                        response.text
                    )
                )

            return state

        return llm_call

    # ============================================================
    # TOOL NODE
    # ============================================================

    def _build_tool_node(self, client, tools):

        tool_map = {
            tool.name: tool
            for tool in tools
        }

        async def tool_exec(state: State) -> State:

            if not state.tool_calls:
                return state

            for call in state.tool_calls:

                tool = tool_map.get(
                    call.name
                )

                # ------------------------------------------------
                # Tool not found
                # ------------------------------------------------

                if tool is None:

                    result = ToolResult(
                        call.id,
                        call.name,
                        f"Error: no tool '{call.name}'",
                        is_error=True,
                    )

                # ------------------------------------------------
                # Execute tool
                # ------------------------------------------------

                else:

                    try:
                        output = await tool.execute(**call.arguments)
                        result = ToolResult(call.id, call.name, output, is_error=False)
                        if getattr(tool, "_last_approval_note", None):
                            state.llm_approval_requests[call.id] = tool._last_approval_note
                    except Exception as e:
                        result = ToolResult(call.id, call.name, f"Error: {e}", is_error=True)

                # Add provider-formatted tool result
                # to conversation history.
                state.messages.append(
                    Message.from_dict(
                        ToolResultFormatter.format(
                            client.provider,
                            result,
                        )
                    )
                )

            return state

        return tool_exec

    # ============================================================
    # APPROVAL NODE
    # ============================================================

    def _build_approval_node(
        self,
        client,
        config: ApprovalConfig,
    ):

        async def _approval(
            state: State,
        ) -> State:

            return await approval_node(
                state,
                client,
                config,
            )

        return _approval

    # ============================================================
    # ROUTING
    # ============================================================

    async def _resolve_next(self, current: str, state) -> str:
        """
        Finds the single edge starting at `current` and resolves it to a
        real node name. Since validate() already guarantees each node has
        at most one static edge OR one router (never both, never more than
        one of either), there's no ambiguity to check here at run time —
        that work is already done.
        """
        matching = [e for e in self.edges if e.start == current]
        if not matching:
            raise ValueError(f"No outgoing edge from node '{current}'.")
        return await matching[0].resolve(state, self)

    

    # ============================================================
    # EXECUTION
    # ============================================================

    async def run(self, state):
            """
            Drives the graph: starts at the entry point (or wherever a previous
            run paused, if resuming), runs each node in turn, and stops when it
            reaches END — or pauses early if a node raises GraphInterrupt.
            """
            if not self._compiled:
                raise RuntimeError("Graph not compiled — pass client/tools via Agent(), or call graph.compile() directly.")
    
            from sparse_ai.graph.graph.graph_interrupt import GraphInterrupt
            from sparse_ai.core.enums import StateEvent
            import inspect
            
            # Resume from a previous pause if one exists, otherwise start fresh.
            current = state.current_node_name or self._entry_point
            
            while current != END:
                try:
                    state.current_node_name = current
                    result = self.nodes[current](state)
                    if inspect.isawaitable(result):
                        result = await result
                    state = result
                    state.executed_nodes.append(current)
                    current = await self._resolve_next(current, state)
    
                except GraphInterrupt as interrupt:
                    state.status = StateEvent.WAITING
                    state.interrupt = interrupt
                    state.current_node_name = current         # exact resume point
                    return state                                # stop here — hand control back to the caller
    
            state.status = StateEvent.DONE
            return state

    

    # ============================================================
    # INSPECTION
    # ============================================================

    def __repr__(self):
        lines = [f"Graph(entry={self._entry_point!r})"]
        lines.append(f"  nodes: {list(self.nodes.keys())}")
        for e in self.edges:
            if e.router:
                lines.append(f"  {e.start} -> <router:{e.router.__name__}>")
            else:
                lines.append(f"  {e.start} -> {e.end}")
        return "\n".join(lines)

    def to_dict(self):
        return {
            "entry_point": self._entry_point,
            "nodes": {
                name: (getattr(func, "__name__", str(func)) if callable(func) else str(func))
                for name, func in self.nodes.items()
            },
            "edges": [
                {"start": e.start, "end": e.end, "router": e.router.__name__ if e.router else None}
                for e in self.edges
            ],
        }

    # ============================================================
    # DISPLAY
    # ============================================================

    def display_graph(self, browser_view: bool = False):
        return GraphDisplay.render(self, force_browser=browser_view)
 
