"""
This module defines the Tool call class , Tool_Call is the AI response which describes that a tool needs to be used. Different providers have their own tool call format which we normalize/generalize.
"""

from dataclasses import dataclass
import json

from sparse_ai.core.enums import Providers



@dataclass
class ToolCall:
    id: str | None          # provider's call id (OpenAI/Claude have this, Gemini often doesn't — can be None or you generate one)
    name: str                # function name to invoke
    arguments: dict          # parsed args, ready to call your Python function with **arguments


#* Contains Functions to normalize a tool call , and Format Tool Result to back-feeding.
class ToolFormator:
    @staticmethod
    def normalize_openai_tool_calls(tool_calls) -> list[ToolCall] | None:
        if not tool_calls:
            return None
        return [
            ToolCall(
                id=tc.id,
                name=tc.function.name,
                arguments=json.loads(tc.function.arguments),  # OpenAI sends args as a JSON string
            )
            for tc in tool_calls
        ]
    @staticmethod
    def normalize_claude_tool_calls(tool_blocks) -> list[ToolCall] | None:
        if not tool_blocks:
            return None
        return [
            ToolCall(
                id=block.id,
                name=block.name,
                arguments=block.input,   # Claude gives this as already-parsed dict
            )
            for block in tool_blocks
        ]
    @staticmethod
    def normalize_gemini_tool_calls(fn_parts) -> list[ToolCall] | None:
        if not fn_parts:
            return None
        return [
            ToolCall(
                id=None,              # Gemini function_call has no call id
                name=fc.name,
                arguments=dict(fc.args),  # already dict-like, but often a proto Struct — cast it
            )
            for fc in fn_parts
        ]
    @staticmethod
    def normalize_tool_call_by_provider(tool_call , provider):
        _tools = None
        if provider in (
    Providers.OPENAI,
    Providers.OPENROUTER,
    Providers.HUGGING_FACE,
    Providers.GROQ,
):
            _tools = ToolFormator.normalize_openai_tool_calls(tool_call)
        elif provider == Providers.GEMINI:
            _tools = ToolFormator.normalize_gemini_tool_calls(tool_call)
        elif provider == Providers.CLAUDE:
            _tools = ToolFormator.normalize_claude_tool_calls(tool_call)
        return _tools


