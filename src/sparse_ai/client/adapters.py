from dataclasses import dataclass
import json
from sparse_ai.core.logging import SparseLogger
from sparse_ai.response.format import LLMResponse
from sparse_ai.response.stream import StreamChunk
from sparse_ai.tools.tool_schemas import ToolSerializer
from sparse_ai.tools.tool_call import ToolCall, ToolFormator
from sparse_ai.client.client_metadata import ClientMetadata

@dataclass
class ClientConfig:
    api_key: str
    model: str
    temperature: float
    retries: int

#* Response Model
# common shape every adapter returns


#! REUSABLE 'OPENAI' compitable CLAS
class OpenAICompatibleAdapter(ClientMetadata):
    def __init__(self, config: ClientConfig, base_url: str, provider: str):
        super().__init__() #* Call Parent Constructor.
        try:
            from openai import AsyncOpenAI
        except ImportError as e:
            raise ImportError(
                f"{provider} support requires the 'openai' package. "
                f"Install 'pip install openai' directly or "
                f"Install it with: pip install sparse-ai[{provider.lower()}]"
            ) from e

        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=base_url,
        )
        self.logger = None

    async def generate(self, messages, tools=None):
        try:
            if self.logger:
                self.logger.log_custom(f"[ADAPTER] Sending {len(messages)} messages to LLM")
            serialized = ToolSerializer.openai_serialize(tools) if tools else None

            response = await self.client.chat.completions.create(
                model=self.config.model, messages=messages, tools=serialized, temperature=self.config.temperature,
            )

            msg = response.choices[0].message

            result = LLMResponse(
                text=msg.content,
                tool_calls=ToolFormator.normalize_openai_tool_calls(msg.tool_calls),
                raw=response,
            )
            self.record_call(response=result) #* METADATA
            #* CUSTOM LOGGER CLASS
            if self.logger:
                query = messages[-1]
                self.logger.log_llm_response(
                    self.config.model,
                    query,
                    response,
                    msg,
                    repr(self)
                )
            return result
        except Exception:
            self.record_call(error=True)
            raise

    #? STREAM RESPONSE
    async def stream(self, messages, tools=None):
        if self.logger:
            self.logger.log_custom(f"[ADAPTER] Starting stream with {len(messages)} messages")
        serialized = ToolSerializer.openai_serialize(tools) if tools else None
        resp_stream = await self.client.chat.completions.create(
            model=self.config.model, messages=messages, tools=serialized,
            temperature=self.config.temperature, stream=True,
        )

        text_parts = []
        tool_calls_acc = {}   # index -> accumulating dict, since tool call args arrive in fragments
        raw_last = None

        async for chunk in resp_stream:
            raw_last = chunk
            delta = chunk.choices[0].delta
            if delta.content:
                text_parts.append(delta.content)
                yield StreamChunk(delta_text=delta.content)
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    acc = tool_calls_acc.setdefault(tc.index, {"id": None, "name": None, "arguments": ""})
                    if tc.id: acc["id"] = tc.id
                    if tc.function.name: acc["name"] = tc.function.name
                    if tc.function.arguments: acc["arguments"] += tc.function.arguments

        tool_calls = [
            ToolCall(id=v["id"], name=v["name"], arguments=json.loads(v["arguments"] or "{}"))
            for v in tool_calls_acc.values()
        ] or None

        final = LLMResponse(text="".join(text_parts) or None, tool_calls=tool_calls, raw=raw_last)
        self.record_call(response=final)
        if self.logger:
            self.logger.log_custom(f"[ADAPTER] Stream completed - Total tokens: {final.raw.usage.total_tokens if hasattr(final.raw, 'usage') else 'N/A'}")
        yield StreamChunk(done=True, final_response=final)

    # OpenAICompatibleAdapter
    def format_assistant_turn(self, response: LLMResponse) -> dict:
        """Builds the assistant turn from a normalized LLMResponse, not the raw
        provider object — works whether response came from generate() or stream()."""
        msg = {"role": "assistant", "content": response.text}
        if response.tool_calls:
            msg["tool_calls"] = [
                {"id": tc.id, "type": "function",
                "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)}}
                for tc in response.tool_calls
            ]
        return msg

    
    
#! GROQ , OPEN ROUTER, HUGGING FACE Using OpenAi compitable design
class OpenAIAdapter(OpenAICompatibleAdapter):
    def __init__(self, config):
        super().__init__(
            config,
            "https://api.openai.com/v1",
            'OpenAI'
        )


class GroqAdapter(OpenAICompatibleAdapter):
    def __init__(self, config):
        super().__init__(
            config,
            "https://api.groq.com/openai/v1",
            'Groq'
        )


class OpenRouterAdapter(OpenAICompatibleAdapter):
    def __init__(self, config):
        super().__init__(
            config,
            "https://openrouter.ai/api/v1",
            'OpenRouter'
        )


class HuggingFaceAdapter(OpenAICompatibleAdapter):
    def __init__(self, config):
        super().__init__(
            config,
            "https://router.huggingface.co/v1",
            'HuggingFace'
        )

class GeminiAdapter(ClientMetadata):
    def __init__(self, config: ClientConfig):
        super().__init__()
        try:
            from google import genai
            from google.genai import types
        except ImportError as e:
            raise ImportError(
                "Gemini support requires the 'google-genai' package. "
                "Install it with: pip install sparse-ai[gemini] "
                "or pip install google-genai."
            ) from e

        self.config = config
        self.genai = genai
        self.types = types
        self.client = genai.Client(api_key=config.api_key)
        self.logger = None

    async def generate(self, contents, tools=None):
        config = None
        try:
            if tools:
                tool_definitions = ToolSerializer.gemini_serialize(tools)
                config = self.types.GenerateContentConfig(
                    tools=[self.types.Tool(**tool_definitions)]
                )
            if self.logger:
                self.logger.log_custom(f"[ADAPTER] Sending {len(contents)} messages to Gemini")
            response = await self.client.aio.models.generate_content(
                model=self.config.model,
                contents=contents,
                config=config,
            )
            content = response.candidates[0].content   # this holds .parts
            parts = content.parts or []

            text_parts = [p.text for p in parts if p.text is not None]
            fn_parts   = [p.function_call for p in parts if p.function_call is not None]

            result =  LLMResponse(
                text="\n".join(text_parts) if text_parts else None,
                tool_calls=ToolFormator.normalize_gemini_tool_calls(fn_parts),
                raw=response,
            )
            self.record_call(result)
            return result
        except Exception:
                    self.record_call(error=True)
                    raise
    
    # GeminiAdapter
    def format_assistant_turn(self, raw) -> dict:
        content = raw.candidates[0].content
        return {"role": content.role, "parts": [p.model_dump() for p in content.parts]}

    async def stream(self, messages, tools=None):
        if self.logger:
            self.logger.log_custom(f"[ADAPTER] Starting Gemini stream with {len(messages)} messages")

        config = None
        if tools:
            tool_definitions = ToolSerializer.gemini_serialize(tools)
            config = self.types.GenerateContentConfig(
                tools=[self.types.Tool(**tool_definitions)]
            )

        text_parts = []
        tool_calls_acc = {}
        raw_last = None

        response_stream = await self.client.aio.models.generate_content(
            model=self.config.model,
            contents=messages,
            config=config,
            stream=True,
        )

        async for chunk in response_stream:
            raw_last = chunk
            if chunk.candidates and chunk.candidates[0].content:
                content = chunk.candidates[0].content
                parts = content.parts or []

                for part in parts:
                    if part.text:
                        text_parts.append(part.text)
                        yield StreamChunk(delta_text=part.text)
                    if part.function_call:
                        func_name = part.function_call.name
                        func_args = part.function_call.args
                        if func_name not in tool_calls_acc:
                            tool_calls_acc[func_name] = {"name": func_name, "args": {}}
                        tool_calls_acc[func_name]["args"].update(func_args)

        tool_calls = [
            ToolCall(id=f"call_{i}", name=v["name"], arguments=v["args"])
            for i, v in enumerate(tool_calls_acc.values())
        ] or None

        final = LLMResponse(text="".join(text_parts) or None, tool_calls=tool_calls, raw=raw_last)
        self.record_call(response=final)
        if self.logger:
            self.logger.log_custom(f"[ADAPTER] Gemini stream completed")
        yield StreamChunk(done=True, final_response=final)
    


class ClaudeAdapter(ClientMetadata):
    def __init__(self, config: ClientConfig):
        super().__init__()
        try:
            from anthropic import AsyncAnthropic
        except ImportError as e:
            raise ImportError(
                "Claude support requires the 'anthropic' package. "
                "Install it with: pip install sparse-ai[claude] or pip install anthropic."
            ) from e
        self.config = config
        self.client = AsyncAnthropic(api_key=config.api_key)   # ✅ async client
        self.logger = None

    async def generate(self, messages, tools=None):
        try:
            if self.logger:
                self.logger.log_custom(f"[ADAPTER] Sending {len(messages)} messages to Claude")
            response = await self.client.messages.create(
                model=self.config.model,
                tools=ToolSerializer.claude_serialize(tools) if tools else None,
                max_tokens=4096,
                messages=messages,
            )
            text_blocks = [b.text for b in response.content if b.type == "text"]
            tool_blocks = [b for b in response.content if b.type == "tool_use"]
            result =  LLMResponse(
                text="\n".join(text_blocks) if text_blocks else None,
                tool_calls=ToolFormator.normalize_claude_tool_calls(tool_blocks),
                raw=    response,
            )
            self.record_call(result)
            return result
        except Exception:
            self.record_call(error=True)
            raise
    # ClaudeAdapter
    def format_assistant_turn(self, raw) -> dict:
        return {"role": "assistant", "content": [b.model_dump() for b in raw.content]}

    async def stream(self, messages, tools=None):
        if self.logger:
            self.logger.log_custom(f"[ADAPTER] Starting Claude stream with {len(messages)} messages")

        text_parts = []
        tool_calls_acc = {}
        raw_last = None

        response_stream = await self.client.messages.create(
            model=self.config.model,
            tools=ToolSerializer.claude_serialize(tools) if tools else None,
            max_tokens=4096,
            messages=messages,
            stream=True,
        )

        async for chunk in response_stream:
            raw_last = chunk
            if chunk.type == "content_block_delta":
                if chunk.delta.type == "text_delta":
                    text_parts.append(chunk.delta.text)
                    yield StreamChunk(delta_text=chunk.delta.text)
            elif chunk.type == "content_block_start":
                if hasattr(chunk, 'content_block') and chunk.content_block.type == "tool_use":
                    tool_id = chunk.content_block.id
                    tool_name = chunk.content_block.name
                    tool_calls_acc[tool_id] = {"id": tool_id, "name": tool_name, "input": {}}
            elif chunk.type == "content_block_stop":
                pass  # Tool use completed
            elif chunk.type == "input_json_delta":
                # Tool input parameters streaming
                if chunk.delta.partial_json:
                    # This is simplified - real implementation would need proper JSON parsing
                    pass

        # Extract tool calls from the final response if available
        tool_blocks = [b for b in raw_last.content if b.type == "tool_use"] if raw_last and hasattr(raw_last, 'content') else []
        tool_calls = [
            ToolCall(id=b.id, name=b.name, arguments=b.input)
            for b in tool_blocks
        ] or None

        final = LLMResponse(text="".join(text_parts) if text_parts else None, tool_calls=tool_calls, raw=raw_last)
        self.record_call(response=final)
        if self.logger:
            self.logger.log_custom(f"[ADAPTER] Claude stream completed")
        yield StreamChunk(done=True, final_response=final)


