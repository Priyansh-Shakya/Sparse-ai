"""
Implementation of special Nodes
"""

from sparse_ai.graph.graph.graph_interrupt import GraphInterrupt
from sparse_ai.state.state import State
from sparse_ai.messages.messages import Message
#! =========== APPROVAL NODE ==================

class ApprovalConfig:
    """
    Marker object produced by Node.approval_node(...). Not executed directly —
    Graph.compile() recognizes it and swaps it for a real async node function.
    Carries the two node names to route to after a human decision, so the
    graph builder can auto-generate this node's router without the user
    having to write one by hand (approval is always a binary decision,
    so this is a genuine structural shortcut, not hidden magic — the
    on_approved/on_rejected values are typed directly by the user).
    """
    def __init__(self, on_approved: str, on_rejected: str, reason: str, generate_verdict: bool, tool_name: str | None = None):
        self.on_approved = on_approved
        self.on_rejected = on_rejected
        self.reason = reason
        self.generate_verdict = generate_verdict,
        self.tool_name = tool_name   # which tool call this approval node is gating, if relevant


async def approval_node(state: State, client, config: ApprovalConfig) -> State:
    if state.approval_response is not None:
        decision = state.approval_response
        verdict = await interpret_decision(state, decision, client)
        state.approval_result = verdict["outcome"]
        state.approval_notes = verdict["notes"]
        state.approval_response = None
        return state

    verdict_text = "Does this look correct, or would you like changes?"   # default, always set first

    if config.generate_verdict:
        relevant_call = next((c for c in state.tool_calls if c.name == config.tool_name), None) if state.tool_calls else None
        inline = state.llm_approval_requests.get(relevant_call.id) if relevant_call else None
        if inline:
            verdict_text = inline
        # else: no inline note captured (provider/tool didn't produce one, or
        # this tool isn't decorated) — fall back to the generic default above,
        # OR optionally call the LLM fallback here if you still want one:
        # else:
        #     phrasing = await client.adapter.generate(...)
        #     verdict_text = phrasing.text or verdict_text

    raise GraphInterrupt(
        reason=config.reason,
        data=state.last_response,
        verdict=verdict_text,
    )

async def interpret_decision(state, decision, client):
    """
    Interprets the human's raw approval_response (e.g. {"choice": "approve", "comment": "..."})
    into a normalized {"outcome": "approve"|"reject", "notes": str}.

    If the human's choice is unambiguous, skip the LLM call entirely — cheaper and
    more reliable than asking a model to re-derive something already explicit.
    Only fall back to the LLM when there's free-text to interpret (e.g. a comment
    that might mean "approve but change X", which isn't a clean binary).
    """
    choice = (decision.get("choice") or "").strip().lower()
    comment = decision.get("comment", "")

    if choice in ("approve", "approved", "yes"):
        return {"outcome": "approve", "notes": comment}
    if choice in ("reject", "rejected", "no"):
        return {"outcome": "reject", "notes": comment}

    # Ambiguous or free-text-only input — ask the LLM to classify it.
    response = await client.adapter.generate(
        messages=[
            Message.system(
                "Classify the human's response to an approval request as exactly "
                "'approve' or 'reject'. Respond with ONLY that one word."
            ).to_dict(),
            Message.user(f"Human said: {choice} {comment}").to_dict(),
        ],
        tools=None,
    )
    outcome = "approve" if "approve" in (response.text or "").lower() else "reject"
    return {"outcome": outcome, "notes": comment}

