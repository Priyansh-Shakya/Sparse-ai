from dataclasses import dataclass
import json
from sparse_ai.core.logging import SparseLogger
from sparse_ai.response.format import LLMResponse
from sparse_ai.tools.tool_schemas import ToolSerializer
from sparse_ai.tools.tool_call import ToolFormator
from sparse_ai.client.client_metadata import ClientMetadata

# at the top of each file — adapters.py, agent.py, tools.py, etc.
logger = SparseLogger.get_logger()

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

    async def generate(self, messages, tools=None):

        print("\n\n\nMESSAGE RECIVED TO ADAPTER:\n",messages)
        print("\n\n\nTOOLS RECIVED BY ADAPTER:\n",tools)
        try:
            self.logger.debug(f"[call :{self.call_count + 1}], sending {len(messages)} messages")
            serialized = ToolSerializer.openai_serialize(tools) if tools else None

            print(json.dumps(serialized, indent=2))  # or self.logger.debug(...)
            SparseLogger.usual(logger , f"SERIALIZED TOOLS: {json.dumps(serialized , indent=2,)}")

            response = await self.client.chat.completions.create(
                model=self.config.model, messages=messages, tools=serialized, temperature=self.config.temperature,
            )
            
            msg = response.choices[0].message

            print("\n\n\n###############################################################ADAPTER GENERATED RESPONSE:\n", msg)
            result = LLMResponse(
                text=msg.content,
                tool_calls=ToolFormator.normalize_openai_tool_calls(msg.tool_calls),
                raw=response,
            )
            self.record_call(response=result) #* METADATA
            #* CUSTOM LOGGER CLASS
            query =  messages[-1]
            SparseLogger.generate_fn_logs(
                                    logger,
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
    # OpenAICompatibleAdapter
    def format_assistant_turn(self, raw) -> dict:
        msg = raw.choices[0].message
        return msg.model_dump(exclude_unset=True)  # already the exact shape needed back

    
    
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

    async def generate(self, contents, tools=None):
        config = None
        try:
            if tools:
                tool_definitions = ToolSerializer.gemini_serialize(tools)
                config = self.types.GenerateContentConfig(
                    tools=[self.types.Tool(**tool_definitions)]
                )
            self.logger.debug(f"[call :{self.call_count + 1}], sending {len(contents)} messages")
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

    async def generate(self, messages, tools=None):
        try:
            self.logger.debug(f"[call :{self.call_count + 1}], sending {len(messages)} messages")
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


