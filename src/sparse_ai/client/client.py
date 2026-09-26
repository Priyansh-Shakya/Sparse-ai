"""
This LLM module is Responsible for providing a invokable LLM Client using Groq API, Model.
Only Handles the invocationa and Generating Text Response.
"""


from sparse_ai.client.client_metadata import ClientMetadata
from sparse_ai.core.enums import Providers
from sparse_ai.client.adapters import ClientConfig, GroqAdapter , OpenAIAdapter , OpenRouterAdapter , ClaudeAdapter , HuggingFaceAdapter , GeminiAdapter


"""
The difference we create from frameworks is that , other asks you to import appropriate module to run the api of which ever provider you are using.
Here , you dont have to do that , we will take a provider field input to determine which provider user is using and internally call the appropriate Client.

"""


class Client:
    """ Client for interacting with an AI provider. 
    Attributes: 
        api: API key used for authentication. 
        provider: Name of the AI provider you are using API_KEY of (openai , gemini , claude , etc). 
        model: Model identifier to use. 
        temp: Sampling temperature controlling response randomness. 
        retries: Number of times to retry a failed request. 
    """
    def __init__(self, api_key:str, provider:Providers ,model:str , temperature:int =0, retries:int =3):
        self.api = api_key
        self.provider = provider
        self.model = model
        self.temp = temperature
        self.retries = retries
        self.adapter = self.create_client()   #! CREATES CLIENT ON INITIATION OF CLIENT CLASS (e.g. client = Client(...)) 



    #? NO MANUAL CREATION NEEDED.
    def create_client(self):
        """Creates a client instance based on the specified provider and configuration."""
        ##* THIS IS THE config which will spread into client: OpenAi(model= ... , api ...) automatically , correct its KEYS.
        config = ClientConfig(
    api_key=self.api,
    model=self.model,
    temperature=self.temp,
    retries=self.retries,
)



        creators = {
            Providers.GROQ: GroqAdapter,
            Providers.OPENAI: OpenAIAdapter,
            Providers.CLAUDE: ClaudeAdapter,
            Providers.GEMINI: GeminiAdapter,
            Providers.HUGGING_FACE: HuggingFaceAdapter,
            Providers.OPENROUTER: OpenRouterAdapter,
        }

        try:
            adapter_cls = creators[self.provider]
        except KeyError:
            raise ValueError(
                f"Unsupported provider: {self.provider}"
            )

        return adapter_cls(config)

    @property
    def total_calls(self) -> int:
        return self.adapter.call_count

    @property
    def stats(self) -> "ClientMetadata":
        return self.adapter   # or expose specific fields if you don't want to leak the whole object



