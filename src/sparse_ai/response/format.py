from typing import Any

from sparse_ai.tools.tools import Tool


class LLMResponse:
    def __init__(self, text: str | None, tool_calls: list[Tool] | None, raw: Any):
        self.text = text
        self.tool_calls = tool_calls
        self.raw = raw

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"text={self.text!r}, "
            f"tool_calls={self.tool_calls!r}"
            f")"
        )
