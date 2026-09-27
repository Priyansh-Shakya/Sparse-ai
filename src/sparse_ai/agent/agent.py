"""This class Builds the Agent that is the Core of every tool we have (messages , tools , states ...etc)"""
from pprint import pformat



from sparse_ai.core.enums import StateEvent
from sparse_ai.state.state import State
from sparse_ai.graph.graph.graph import Graph
from sparse_ai.messages.messages import Message
from sparse_ai.graph.graph.default import default_agent_graph
from sparse_ai.core.logging import SparseLogger


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
        logging (bool):
            Whether to enable detailed logging throughout agent execution.
            When True, logs agent queries, node executions, LLM responses,
            tool calls, and other events. When False, only final output is shown.
        logging (bool):
            Whether to enable detailed logging throughout agent execution.
        logger (SparseLogger):
            Logger instance used throughout the framework.

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
        ...     logging=True,
        ... )
        >>>
        >>> response = await agent.run("What is the weather today?")
    """
    def __init__(self, client, messages: list,
                  tools=None, 
                  graph: "Graph | None" = None,
                 stream = False,
                 state: "State | None" = None, 
                 auto_handle_interrupts:bool = False,
                   retries: int = 3,
                   logging: bool = False):
        self.logging = logging
        self.logger = SparseLogger(enabled=logging)
        self.client = client
        self.messages = messages
        self.tools = tools or []
        self._provider = self.client.provider
        self.retries = retries
        self.state = state or State()          # fresh instance every time, not a shared default
        self.state.agent_retries = self.retries
        self.auto_handle_interrupts = auto_handle_interrupts
        # Query-level statistics
        self.query_stats = {
            'llm_calls': 0,
            'tools_executed': 0,
            'nodes_executed': 0,
            'total_tokens': 0
        }
        # Pass logger to state
        self.state.logger = self.logger
        # Pass logger to client and adapter
        self.client.logger = self.logger
        if hasattr(self.client, 'adapter'):
            self.client.adapter.logger = self.logger
        # Set stream on client
        if hasattr(self.client, 'stream_enabled'):
            self.client.stream_enabled = stream
        # Compile graph with logger
        self.graph = (graph or default_agent_graph()).compile(client=self.client, tools=self.tools, logger=self.logger)


    async def run(self, query: str, stream=None):
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
            stream (bool, optional):
                Whether to stream the response. Overrides the agent's default
                stream setting for this call only.

        Returns:
            str | GraphInterrupt:
                The final text response when execution completes, or a
                `GraphInterrupt` when execution is paused for external input and
                automatic interrupt handling is disabled.

        Example:
            >>> response = await agent.run("What files are available?")
            >>> print(response)
        """
        # Reset query-level statistics
        self.query_stats = {
            'llm_calls': 0,
            'tools_executed': 0,
            'nodes_executed': 0,
            'total_tokens': 0
        }

        self.logger.log_agent_start(query)
        if self.tools:
            self.logger.log_tools_available(self.tools)
        self.messages.append(Message.user(query))
        self.state.messages = self.messages     # sync — self.messages stays the one source of truth
        self.state.query_stats = self.query_stats  # Pass stats to state
        self.logger.log_state(self.state)
        final_state = await self.graph.run(self.state, self.query_stats)
        self.state = final_state                    # ← must happen
        self.messages = final_state.messages   # sync back, in case a node appended tool/assistant turns
        self.state.stream = stream   # None if caller doesn't want streaming for this call

        #* CHECKING INTERRUPT
        if final_state.interrupt is not None:
            response = final_state.interrupt
            if self.auto_handle_interrupts: #? WHEN AGENT(auto_handle_interrupts=True)
                return await self.check_interrupt(response=response)
            return response   # caller wants to handle it themselves — e.g. a real UI, not input()

        # Log query summary
        self.query_stats['final_response'] = final_state.last_response.text if final_state.last_response else 'No response'
        self.query_stats['state'] = final_state
        self.logger.log_query_summary(query, self.query_stats, show_state=False)

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
            self.logger.log_interrupt(response.reason, response.data)
            print(f"Reason: {response.reason}")
            print(f"Question: {response.verdict}")

            choice = input("approve or reject? ")
            comment = input("any comment? ")

            response = await self.resume({"choice": choice, "comment": comment})

        return response   # once it's no longer a GraphInterrupt, it's the final text answer