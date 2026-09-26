"""This class Builds the Agent that is the Core of every tool we have (messages , tools , states ...etc)"""
from pprint import pformat



from sparse_ai.core.enums import StateEvent
from sparse_ai.state.state import State
from sparse_ai.graph.graph.graph import Graph
from sparse_ai.messages.messages import Message
from sparse_ai.graph.graph.default import default_agent_graph


# at the top of each file — adapters.py, agent.py, tools.py, etc.
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class Agent:
    """
    High-level interface for running an agent through a compiled execution graph.

    An `Agent` combines an LLM client, conversation messages, optional tools,
    and a graph that controls the agent's execution flow. If no graph is
    provided, the framework uses its default agent graph.

    The agent maintains a `State` instance across graph execution, allowing
    nodes to share messages, tool calls, responses, interrupts, and other
    runtime information.

    Agent execution is asynchronous. If graph execution is interrupted for
    human input, the agent can either return the interrupt to the caller or
    handle it automatically when `auto_handle_interrupts=True`.

    Attributes:
        client:
            LLM client used by the agent.
        messages (list):
            Conversation messages maintained by the agent.
        tools (list):
            Tools available to the agent's graph.
        graph (Graph):
            Compiled execution graph used to run the agent.
        state (State):
            Runtime state shared across graph execution.
        retries (int):
            Maximum number of retries configured for agent execution.
        auto_handle_interrupts (bool):
            Whether pending graph interrupts should be handled automatically
            through `check_interrupt()`.

    Methods:
        run(query):
            Run the agent with a new user query.
        resume(approval_response):
            Resume graph execution after an interrupt.
        check_interrupt(response):
            Interactively handle pending graph interrupts until execution
            produces a final response.

    Example:
        >>> agent = Agent(
        ...     client=client,
        ...     messages=[],
        ...     tools=[search_tool],
        ... )
        >>>
        >>> response = await agent.run("What is the weather today?")
    """
    def __init__(self, client, messages: list, tools=None, graph: "Graph | None" = None,
                 state: "State | None" = None,auto_handle_interrupts:bool = False, retries: int = 3):
        self.client = client
        self.messages = messages
        self.tools = tools or []
        self._provider = self.client.provider
        self.graph = (graph or default_agent_graph()).compile(client=self.client, tools=self.tools)
        self.retries = retries
        self.state = state or State()          # fresh instance every time, not a shared default
        self.state.agent_retries = self.retries
        self.auto_handle_interrupts = auto_handle_interrupts

    async def run(self, query: str):
        """
        Run the agent with a new user query.

        The query is added to the agent's conversation messages and execution
        is delegated to the compiled graph. The graph operates on the agent's
        current `State`, which is updated with the final execution state.

        If graph execution produces a `GraphInterrupt`, the interrupt is either
        returned to the caller or handled automatically through
        `check_interrupt()` when `auto_handle_interrupts` is enabled.

        Args:
            query (str):
                New user message to send to the agent.

        Returns:
            str | GraphInterrupt:
                The final text response when execution completes, or a
                `GraphInterrupt` when execution is paused for external input and
                automatic interrupt handling is disabled.

        Example:
            >>> response = await agent.run("What files are available?")
            >>> print(response)
        """
        print("=================================AGENT RUNNING=======================================")
        self.messages.append(Message.user(query))
        self.state.messages = self.messages     # sync — self.messages stays the one source of truth
        print("================================= STATE =================================================\n",self.state.__repr__())
        final_state = await self.graph.run(self.state)
        self.state = final_state                    # ← must happen 
        self.messages = final_state.messages   # sync back, in case a node appended tool/assistant turns

        #* CHECKING INTERRUPT
        if final_state.interrupt is not None:
            response = final_state.interrupt
            if self.auto_handle_interrupts: #? WHEN AGENT(auto_handle_interrupts=True)
                return await self.check_interrupt(response=response)
            return response   # caller wants to handle it themselves — e.g. a real UI, not input()

        return final_state.last_response.text


    #* RESUME GRAPH
    async def resume(self, approval_response: dict):
        if self.state.status != StateEvent.WAITING:
            raise RuntimeError("No pending interrupt to resume — call run() first.")

        self.state.approval_response = approval_response
        self.state.interrupt = None   # clear the old one before resuming, so a fresh one (or none) is accurate
        final_state = await self.graph.run(self.state)
        self.state = final_state
        self.messages = final_state.messages

        if final_state.interrupt is not None:
            return final_state.interrupt
        return final_state.last_response.text


    async def check_interrupt(self, response):
        from sparse_ai.graph.graph.graph_interrupt import GraphInterrupt

        while isinstance(response, GraphInterrupt):
            print(f"Reason: {response.reason}")
            print(f"Data: {response.data}")
            print(f"Question: {response.verdict}")

            choice = input("approve or reject? ")
            comment = input("any comment? ")

            response = await self.resume({"choice": choice, "comment": comment})

        return response   # once it's no longer a GraphInterrupt, it's the final text answer