"""
This module is responsible for creatig and managing Nodes For Graph. Create and Format etc...
"""

# Node("NAME" , "FUNCTION/ETC")

# Since Nodes are independent and can be declared in any order irrespective of their order in Graph because that is decided by Edges going to nodes - a node list can take nodes is any order.

from sparse_ai.graph.nodes.special_nodes import ApprovalConfig


class Node:
    _LLM_CALL = "__llm_call__" #* RESERVED KEYWORDS FOR MATCHING. 
    _TOOL_EXEC = "__tool_exec__"

    """
    Represents a node in the graph.

    A node associates a unique name with a callable that is executed when
    the graph reaches that node.

    The `func` argument normally contains a user-defined function. However,
    `llm_call()` and `tool_exec()` can be used to add the framework's built-in
    LLM and tool-execution nodes without providing a custom function.

    These built-in nodes are represented internally by reserved sentinel
    values. When `Graph.compile()` is called, the graph resolves these
    sentinels to the framework's actual LLM and tool-execution functions.

    Attributes:
        name (str): Unique name used to identify the node in the graph.
        func (callable | str): Function executed by the node, or a reserved
            sentinel returned by `llm_call()` / `tool_exec()`.

    Example:
        >>> Node("process", process_data)
        >>> Node("llm", Node.llm_call())
        >>> Node("tools", Node.tool_exec())
    """

    def __init__(self, name, func):
        self.name = name
        self.func = func

    @staticmethod
    def llm_call():
        """
        Return the reserved marker for the framework's built-in LLM node.

        This does not execute an LLM call or create a custom node function.
        It only identifies the node as an LLM node. During `Graph.compile()`,
        the graph resolves this marker to the framework's configured LLM
        execution function.

        Returns:
            str: Reserved LLM node marker.

        Example:
            >>> Node("llm", Node.llm_call())
        """
        return Node._LLM_CALL

    @staticmethod
    def tool_exec():
        """
        Return the reserved marker for the framework's built-in tool node.

        This does not execute a tool directly. It identifies the node as the
        framework's tool-execution node. During `Graph.compile()`, the graph
        resolves this marker to the framework's tool execution function.

        Returns:
            str: Reserved tool-execution node marker.

        Example:
            >>> Node("tools", Node.tool_exec())
        """
        return Node._TOOL_EXEC

    @staticmethod
    def approval_node(
        on_approved: str,
        on_rejected: str,
        reason: str = "approval_required",
        generate_verdict: bool = True,
        tool_name: str | None = None
    ):
        """Create a configuration for a framework-managed human approval node.

        This does not execute an approval directly. It defines how the graph
        should handle a human approval decision. During `Graph.compile()`, the
        returned `ApprovalConfig` is recognized and resolved to the framework's
        approval-handling node.

        Args:
            on_approved (str): Name of the node to execute when the request is
                approved (Carry Forward).
            on_rejected (str): Name of the node to execute when the request is
                rejected (Do Over).
            reason (str): Reason presented for requesting human approval.
                Defaults to "approval_required".
            generate_verdict (bool): If True, the framework asks the LLM to phrase the approval
                question dynamically based on what's being approved; if False, a
                generic fixed question is used instead (cheaper, no extra LLM call).
            tool_name (str): "Name of the tool of which's result needs approval"

        Returns:
            ApprovalConfig: Configuration describing the approval node and its
            possible transitions.

        Example:
            >>> Node(
            ...     "approve_student",
            ...     Node.approval_node(
            ...         on_approved="create_student",
            ...         on_rejected="end"
            ...     )
            ... )"""
        
        return ApprovalConfig(on_approved, on_rejected, reason, generate_verdict, tool_name)



    #? FOR DEFAULT GRAPH
    @staticmethod
    def default_router():
        """No client dependency needed — this can be used directly, no compile step required."""
        def _route(state):
            return "has_tools" if state["last_response"].tool_calls else "done"
        return _route
    
