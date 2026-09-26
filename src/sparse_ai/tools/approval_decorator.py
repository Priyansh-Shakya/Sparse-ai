DEFAULT_APPROVAL_INSTRUCTION = (
    "Before calling this tool, briefly state what result or change this call "
    "will produce, so a human can decide whether to proceed or ask for changes."
)

def approval_request(instruction: str | None = None):
    """
    Marks a tool as needing human approval. Adds a `__approval_request__`
    field to the TOOL'S SCHEMA only — the wrapped function's real signature
    and behavior are never touched. The LLM fills this field in as part of
    the normal tool call (works on every provider, since it's just another
    argument — no dependency on text-alongside-tool-call support).
    """
    def decorator(func):
        func._approval_instruction = instruction or (
            "Briefly state what result or change this call will produce."
        )
        func._needs_approval = True
        return func

    if callable(instruction):   # bare @approval_request, and () both supported.
        func = instruction
        instruction = None
        return decorator(func)

    return decorator