

import logging
import time

from sparse_ai.response.format import LLMResponse


class ClientMetadata:
    """Tracks per-adapter runtime stats. Every adapter inherits this — one source of truth."""
    def __init__(self):
        self.call_count: int = 0
        self.error_count: int = 0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.last_call_at: float | None = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def record_call(self, response: "LLMResponse | None" = None, error: bool = False):
        self.call_count += 1
        self.last_call_at = time.time()
        if error:
            self.error_count += 1
        elif response is not None:
            usage = getattr(response.raw, "usage", None)   # provider-specific, may not always exist
            if usage:
                self.total_input_tokens += getattr(usage, "input_tokens", getattr(usage, "prompt_tokens", 0)) or 0
                self.total_output_tokens += getattr(usage, "output_tokens", getattr(usage, "completion_tokens", 0)) or 0

    def __repr__(self):
        return f"{self.__class__.__name__}(calls={self.call_count}, errors={self.error_count}, total_input_tokens={self.total_input_tokens}, total_output_tokens={self.total_output_tokens}, last_call_at={self.last_call_at})"