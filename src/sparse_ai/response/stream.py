

from sparse_ai.response.format import LLMResponse

# Stream Class handled partial token (response) emitted by Model.
class StreamChunk:
    def __init__(self, delta_text: str | None = None, done: bool = False, final_response: "LLMResponse | None" = None):
        self.delta_text = delta_text          # incremental text, as it arrives
        self.done = done                       # True on the last chunk of this turn
        self.final_response = final_response   # populated only when done=True — the complete LLMResponse