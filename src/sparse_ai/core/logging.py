import logging
from textwrap import wrap
from pprint import pformat

class SparseLogger:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.logger = logging.getLogger(__name__)

        # Always suppress HTTP library logs regardless of enabled state
        for logger_name in ["httpcore", "httpx", "httpcore2", "httpx2", "openai"]:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)
            logging.getLogger(logger_name).propagate = False

        if self.enabled:
            # Configure root logger for our debug output
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler()
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
            handler.setFormatter(formatter)
            # Remove existing handlers to avoid duplicates
            root_logger.handlers.clear()
            root_logger.addHandler(handler)
        else:
            # When disabled, suppress all logs
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.CRITICAL)
            root_logger.handlers.clear()

    def _format_box_text(self, text, width=56):
        if not text:
            return "║ <none>" + " " * 49 + "║"
        return "\n".join(
            f"║ {line:<56} ║"
            for line in wrap(str(text), width=56)
        )

    def _format_box_text_pprint(self, text, width=56):
        if not text:
            return "║ <none>" + " " * 49 + "║"
        formatted = pformat(text, width=width-4)
        return "\n".join(
            f"║ {line:<56} ║"
            for line in wrap(formatted, width=56)
        )

    def log_agent_start(self, query: str):
        if not self.enabled:
            return
        self.logger.debug(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                    AGENT EXECUTION START                     ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ USER QUERY                                                   ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{self._format_box_text(query)}\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )

    def log_state(self, state):
        if not self.enabled:
            return
        self.logger.debug(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                      CURRENT STATE                           ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{self._format_box_text_pprint(state)}\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )

    def log_node_execution(self, node_name: str):
        if not self.enabled:
            return
        self.logger.debug(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                      NODE EXECUTION                          ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"║ Node: {node_name:<52} ║\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )

    def log_llm_response(self, model, query, response, msg, metadata="N/A"):
        if not self.enabled:
            return
        self.logger.debug(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                       LLM RESPONSE                          ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"║ Model: {model:<52} ║\n"
            f"║ Finish reason: {response.choices[0].finish_reason!s:<43} ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ User Query                                                   ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{self._format_box_text(query)}\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ CONTENT                                                      ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{self._format_box_text(msg.content)}\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ TOOL CALLS                                                   ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{self._format_box_text_pprint(msg.tool_calls)}\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ METADATA                                                     ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{self._format_box_text(metadata)}\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )

    def log_tool_call(self, tool_name: str, arguments: dict):
        if not self.enabled:
            return
        self.logger.debug(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                       TOOL CALL                              ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"║ Tool: {tool_name:<52} ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ ARGUMENTS                                                    ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{self._format_box_text_pprint(arguments)}\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )

    def log_tool_result(self, tool_name: str, result, is_error: bool = False):
        if not self.enabled:
            return
        status = "ERROR" if is_error else "SUCCESS"
        self.logger.debug(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                      TOOL RESULT                            ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"║ Tool: {tool_name:<52} ║\n"
            f"║ Status: {status:<50} ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ RESULT                                                       ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{self._format_box_text_pprint(result)}\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )

    def log_graph_routing(self, from_node: str, to_node: str):
        if not self.enabled:
            return
        self.logger.debug(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                      GRAPH ROUTING                           ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"║ From: {from_node:<52} ║\n"
            f"║ To:   {to_node:<52} ║\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )

    def log_approval_request(self, reason: str, verdict: str):
        if not self.enabled:
            return
        self.logger.debug(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                   APPROVAL REQUEST                           ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"║ Reason: {reason:<50} ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ QUESTION                                                     ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{self._format_box_text(verdict)}\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )

    def log_approval_decision(self, decision: str, notes: str = ""):
        if not self.enabled:
            return
        self.logger.debug(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                   APPROVAL DECISION                          ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"║ Decision: {decision:<48} ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ NOTES                                                        ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{self._format_box_text(notes)}\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )

    def log_message_added(self, role: str, content_preview: str):
        if not self.enabled:
            return
        self.logger.debug(
            f"[MESSAGE ADDED] Role: {role}, Content: {content_preview[:100]}..."
        )

    def log_interrupt(self, reason: str, data):
        if not self.enabled:
            return
        self.logger.debug(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                     GRAPH INTERRUPT                          ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"║ Reason: {reason:<50} ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ DATA                                                         ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{self._format_box_text_pprint(data)}\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )

    def log_custom(self, message: str):
        if not self.enabled:
            return
        self.logger.debug(message)

    def log_tools_available(self, tools: list):
        if not self.enabled:
            return
        self.logger.debug(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                    TOOLS AVAILABLE                           ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"║ Total Tools: {len(tools):<48} ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ TOOL NAMES                                                   ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{self._format_box_text_pprint([tool.name for tool in tools])}\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )

    def log_query_summary(self, query: str, stats: dict, show_state: bool = False):
        if not self.enabled:
            return
        final_response = stats.get('final_response', 'N/A')
        if final_response is None:
            final_response = 'No response generated'
        self.logger.debug(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                      QUERY SUMMARY                           ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"║ Total LLM Calls: {stats.get('llm_calls', 0):<44} ║\n"
            f"║ Tools Executed: {stats.get('tools_executed', 0):<44} ║\n"
            f"║ Nodes Executed: {stats.get('nodes_executed', 0):<44} ║\n"
            f"║ Total Tokens: {stats.get('total_tokens', 'N/A'):<43} ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ FINAL RESPONSE                                               ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{self._format_box_text(final_response)}\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )
        if show_state and stats.get('state'):
            self.logger.log_state(stats['state'])

    @staticmethod
    def get_logger():
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(levelname)s:%(name)s:%(message)s"
        )
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)
        return logger

    @staticmethod
    def generate_fn_logs(logger, model, query, response, msg, metadata="N/A"):
        def format_box_text(text, width=56):
            if not text:
                return "║ <none>" + " " * 49 + "║"
            return "\n".join(
                f"║ {line:<56} ║"
                for line in wrap(str(text), width=56)
            )
        logger.debug(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                       LLM RESPONSE                          ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"║ Model: {model:<52} ║\n"
            f"║ Finish reason: {response.choices[0].finish_reason!s:<43} ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ User Query                                                   ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{format_box_text(query)}\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ CONTENT                                                      ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{format_box_text(msg.content)}\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ TOOL CALLS                                                   ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{format_box_text(msg.tool_calls)}\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ METADATA                                                     ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{format_box_text(metadata)}\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )

    @staticmethod
    def usual(logger, msg):
        logger.debug(msg)