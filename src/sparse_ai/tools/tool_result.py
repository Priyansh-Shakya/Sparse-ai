"""
This module Specifys Tool Result Format for specific Providers to back feed to ai.
"""


from dataclasses import dataclass
from typing import Any

from sparse_ai.core.enums import Providers


@dataclass
class ToolResult:
    tool_call_id: str | None   # carry this through, even though Gemini often has none
    name: str
    result: Any
    is_error: bool = False



#* OpenAI/Groq/OpenRouter/HuggingFace: role: "tool" (own role)
#* Claude: role: "user", with a tool_result content block inside
#* Gemini: role: "user" (current google-genai SDK), with a function_response part inside

class ToolResultFormatter:
    @staticmethod
    def format(provider: Providers, result: ToolResult) -> dict:
        # in ToolResultFormatter
        if provider in (Providers.OPENAI, Providers.OPENROUTER, Providers.GROQ, Providers.HUGGING_FACE):
            return ToolResultFormatter.to_openai(result)
        elif provider == Providers.GEMINI:
            return ToolResultFormatter.to_gemini(result)
        elif provider == Providers.CLAUDE:
            return ToolResultFormatter.to_claude(result)
        else:
            raise ValueError(f"Unsupported Provider Type: {provider}")
    @staticmethod
    def to_openai(result: ToolResult) -> dict:
        content = f"Error: {result.result}" if result.is_error else str(result.result)
        return {
            "name": result.name,
            "role": "tool",
            "tool_call_id": result.tool_call_id,
            "content": content,
        }

    @staticmethod
    def to_claude(result: ToolResult) -> dict:
        block = {
            "type": "tool_result",
            "tool_use_id": result.tool_call_id,
            "content": str(result.result),
            
        }
        if getattr(result, "is_error", False):
            block["is_error"] = True
        return {"role": "user", "content": [block]}

    @staticmethod
    def to_gemini(result: ToolResult) -> dict:
        response_payload = {"error": str(result.result)} if result.is_error else {"result": result.result}
        return {
            "role": "user",
            "parts": [
                {"function_response": {"name": result.name, "response": response_payload}}
            ],
        }