from enum import Enum


#* The Following Providers are supported by our client
class Providers(Enum):
    GROQ= "groq"
    OPENAI = "openai"
    CLAUDE="claude"
    GEMINI="gemini"
    HUGGING_FACE="hugging_face"
    OPENROUTER="openrouter"


#* State Event Enums
class StateEvent(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    WAITING = "waiting"
    DONE = "done"


#* EVENT Enum used for Routing logic condition writing.
class Event(Enum):
    # Messages / responses
    MESSAGES = "messages"
    LAST_RESPONSE = "last_response"

    # Tools
    TOOL_CALLS = "tool_calls"
    TOOL_RESULTS = "tool_results"

    # Runtime
    CURRENT_NODE_NAME = "current_node_name"
    STATUS = "status"
    RUN_ID = "run_id"
    EXECUTED_NODES = "executed_nodes"

    # Retries
    NODE_RETRIES = "node_retries"
    AGENT_RETRIES = "agent_retries"

    # Approval
    NEEDS_APPROVAL = "needs_approval"
    INTERRUPT = "interrupt"
    APPROVAL_RESPONSE = "approval_response"
    APPROVAL_RESULT = "approval_result"
    APPROVAL_NOTES = "approval_notes"