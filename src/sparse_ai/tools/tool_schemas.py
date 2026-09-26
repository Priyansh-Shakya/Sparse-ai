"""
This module contains functions which will be used by Adapter Classes to convert the Framework Tool objects into native provider specific tool definition before passing tools to the client.
"""

# OpenAI Tool schema

from sparse_ai.tools.tools import Tool
class ToolSerializer:
    @staticmethod
    def openai_serialize(tools: list):
        tool_definitions = Tool.serialize_tool(tools)

        return [
            {
                "type": "function",
                "function": tool_definition,
            }
            for tool_definition in tool_definitions
        ]

    @staticmethod
    def claude_serialize(tools: list):
      tool_defs = Tool.serialize_tool(tools)

      return [
          {
              "name": tool["name"],
              "description": tool["description"],
              "input_schema": tool["parameters"],
          }
          for tool in tool_defs
      ]

    @staticmethod
    def gemini_serialize(tools):
        tool_defs = Tool.serialize_tool(tools)

        return {
            "function_declarations": tool_defs
        }

    @staticmethod
    def hugging_face_serialize(tools: list):
        """Uses OpenAi serializer underneath Because they share same Schema."""
        return ToolSerializer.openai_serialize(tools)

    @staticmethod
    def openrouter_serialize(tools: list):
        """Uses OpenAi serializer underneath Because they share same Schema."""
        return ToolSerializer.openai_serialize(tools)

    @staticmethod
    def groq_serialize(tools: list):
        """Uses OpenAi serializer underneath Because they share same Schema."""
        return ToolSerializer.openai_serialize(tools)
    

