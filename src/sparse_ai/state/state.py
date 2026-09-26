from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sparse_ai.graph.graph.graph_interrupt import GraphInterrupt


class State:
    """
The one shared object that flows through every node in a graph run.
Built once per Agent.run() call, mutated node to node, returned at the end.

Supports both attribute access (state.messages) and dict-style access
(state["messages"], state.get("tool_calls")) so existing code and any
custom user-written nodes keep working without forcing a rewrite.

Framework fields:

    messages (list[Message]):
        Full conversation history so far, in the framework's internal
        Message format — not raw provider dictionaries.

    last_response (LLMResponse | None):
        The most recent model turn. See LLMResponse for its shape.

        - last_response.text:
            The model's final text answer, or None if this turn was a
            tool call instead.

        - last_response.tool_calls:
            List[ToolCall] requested by the model this turn, or None if
            it answered with plain text instead.

        Each ToolCall has .id, .name, and .arguments (already parsed into
        a dict — no string parsing needed).

        A node/router should check `.tool_calls` before assuming `.text`
        is populated, or vice versa — a turn is one or the other, and
        neither is guaranteed to be present on every turn.

    tool_calls (list[ToolCall] | None):
        Convenience mirror of last_response.tool_calls, set by the
        LLM-call node so tool execution and routers don't need to reach
        through last_response every time.

    tool_results (list):
        Results produced by tool execution.

    approval_response:
        Raw response/data associated with an approval interrupt.

    approval_result:
        Result of an approval decision, typically "approve" or "reject".

    approval_notes:
        Free-text reason, feedback, or additional request supplied with
        the approval decision.

Custom fields:

    custom_fields (dict):
        User-owned runtime storage for application-specific values that
        are useful across nodes, routers, validators, or custom logic.

        Framework fields intentionally cover only state that the framework
        itself needs. Use custom_fields when your application needs
        additional state that is specific to your graph or workflow.

        Example:

            state.custom_fields["needs_sql_validation"] = True

        For reads, prefer `.get()` with a default when the field may not
        have been initialized yet:

            needs_validation = state.custom_fields.get(
                "needs_sql_validation",
                False,
            )

        This avoids KeyError when a router/node runs before another node
        has created the field.

        custom_fields is a separate namespace from the framework's real
        State attributes. For example,

            state.tool_calls

        and

            state.custom_fields["tool_calls"]

        are completely different values. Users should nevertheless avoid
        reusing framework field names inside custom_fields when possible
        to prevent confusion.

Internal runtime data:

    current_node_name:
        Name of the node currently being executed.

    status:
        Current graph run status, such as "running", "waiting", or "paused".

    run_id:
        Identifier for this graph run.

    executed_nodes:
        Nodes that have been executed during this run.

Retries:

    node_retries:
        Retry information tracked per node.

    agent_retries:
        Retry configuration/state associated with the Agent.

Approval / interruption:

    interrupt:
        GraphInterrupt instance when execution is paused for external
        input or human approval; otherwise None.
"""
 

    def __init__(self, messages=None, custom_fields: dict | None = None):
        self.messages = messages or [] 
        self.last_response = None
        self.tool_calls = None
        self.tool_results = []

        #* Internal runtime data
        self.current_node_name = None
        self.status = None    # 'ENUMS': "running" , "waiting" , "paused" | Initially => None
        self.run_id = None
        self.executed_nodes = []

        #* Retries
        self.node_retries = {}
        self.agent_retries = None #* Fields by agent

        #* Approval fields
        self.interrupt: "GraphInterrupt | None" = None
        self.approval_response = None 
        self.approval_result = None 
        self.approval_notes = None  # Reason of Approval/Rejection or extra Request with it.
        self.llm_approval_requests: dict[str, str] = {}   # {"tool_call_id" : "approval explanation text"}

        #* Custom fields by Users...
        self.custom_fields = custom_fields or {}


 
    def get(self, key, default=None):
        return getattr(self, key, default)
 
    def __getitem__(self, key):
        return getattr(self, key)
 
    def __setitem__(self, key, value):
        setattr(self, key, value)
 
    def __repr__(self):
        return (
            f"State("
            f"messages={self.messages!r}, "
            f"last_response={self.last_response!r}, "
            f"tool_calls={self.tool_calls!r}, "
            f"tool_results={self.tool_results!r}, "
            f"current_node_name={self.current_node_name!r}, "
            f"status={self.status!r}, "
            f"run_id={self.run_id!r}, "
            f"executed_nodes={self.executed_nodes!r}, "
            f"node_retries={self.node_retries!r}, "
            f"agent_retries={self.agent_retries!r}, "
            f"interrupt={self.interrupt!r}, "
            f"approval_response={self.approval_response!r}, "
            f"approval_result={self.approval_result!r}, "
            f"approval_notes={self.approval_notes!r}, "
            f"llm_approval_requests={self.llm_approval_requests!r}, "
            f"custom_fields={self.custom_fields!r}"
            f")"
        )