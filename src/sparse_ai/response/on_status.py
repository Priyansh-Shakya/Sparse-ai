class StatusEvent:
    """A generic status update the framework can hand to on_status. Kept minimal
    and provider-agnostic — callers decide how to render it (HUD text, icon, etc.)."""
    def __init__(self, kind: str, tool_name: str | None = None, detail: str | None = None):
        self.kind = kind            # e.g. "tool_call" 
        self.tool_name = tool_name  # e.g. "execute_sql"
        self.detail = detail        # optional human-readable text, framework-provided default