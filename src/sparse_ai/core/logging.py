import logging
from textwrap import wrap
from pprint import pformat


class LogCapture:
    """Captures logs regardless of logging flag for manual inspection."""
    
    def __init__(self):
        self.logs = []
    
    def add(self, log_type: str, content):
        """Add a log entry with type and content."""
        self.logs.append({"type": log_type, "content": content})
    
    def clear(self):
        """Clear all logs."""
        self.logs = []
    
    def __str__(self):
        """Return formatted boxed display of all logs."""
        if not self.logs:
            return "No logs captured."
        
        output = []
        for log in self.logs:
            log_type = log["type"]
            content = log["content"]
            
            if log_type == "agent_start":
                output.append(
                    "\n"
                    "╔══════════════════════════════════════════════════════════════╗\n"
                    "║                    AGENT EXECUTION START                     ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    "║ USER QUERY                                                   ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"{self._format_box_text(content)}\n"
                    "╚══════════════════════════════════════════════════════════════╝"
                )
            elif log_type == "tools_available":
                output.append(
                    "\n"
                    "╔══════════════════════════════════════════════════════════════╗\n"
                    "║                    TOOLS AVAILABLE                           ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"║ {content:<56} ║\n"
                    "╚══════════════════════════════════════════════════════════════╝"
                )
            elif log_type == "state":
                output.append(
                    "\n"
                    "╔══════════════════════════════════════════════════════════════╗\n"
                    "║                      CURRENT STATE                           ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"{self._format_box_text_pprint(content)}\n"
                    "╚══════════════════════════════════════════════════════════════╝"
                )
            elif log_type == "node_execution":
                output.append(
                    "\n"
                    "╔══════════════════════════════════════════════════════════════╗\n"
                    "║                      NODE EXECUTION                          ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"║ Node: {content:<52} ║\n"
                    "╚══════════════════════════════════════════════════════════════╝"
                )
            elif log_type == "llm_response":
                # content is expected to be a dict with llm response data
                data = content if isinstance(content, dict) else {}
                output.append(
                    "\n"
                    "╔══════════════════════════════════════════════════════════════╗\n"
                    "║                       LLM RESPONSE                          ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"║ Model: {data.get('model', 'N/A'):<52} ║\n"
                    f"║ Finish reason: {data.get('finish_reason', 'N/A'):<43} ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    "║ USER QUERY                                                   ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"{self._format_box_text(data.get('query', 'N/A'))}\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    "║ CONTENT                                                      ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"{self._format_box_text(data.get('content', 'N/A'))}\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    "║ TOOL CALLS                                                   ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"{self._format_box_text_pprint(data.get('tool_calls', 'N/A'))}\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    "║ METADATA                                                     ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"{self._format_box_text(data.get('metadata', 'N/A'))}\n"
                    "╚══════════════════════════════════════════════════════════════╝"
                )
            elif log_type == "tool_call":
                # content is expected to be a dict with tool_name and arguments
                data = content if isinstance(content, dict) else {}
                output.append(
                    "\n"
                    "╔══════════════════════════════════════════════════════════════╗\n"
                    "║                       TOOL CALL                              ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"║ Tool: {data.get('tool_name', 'N/A'):<52} ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    "║ ARGUMENTS                                                    ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"{self._format_box_text_pprint(data.get('arguments', 'N/A'))}\n"
                    "╚══════════════════════════════════════════════════════════════╝"
                )
            elif log_type == "tool_result":
                # content is expected to be a dict with tool_name, result, is_error
                data = content if isinstance(content, dict) else {}
                status = "ERROR" if data.get('is_error', False) else "SUCCESS"
                output.append(
                    "\n"
                    "╔══════════════════════════════════════════════════════════════╗\n"
                    "║                      TOOL RESULT                            ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"║ Tool: {data.get('tool_name', 'N/A'):<52} ║\n"
                    f"║ Status: {status:<50} ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    "║ RESULT                                                       ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"{self._format_box_text_pprint(data.get('result', 'N/A'))}\n"
                    "╚══════════════════════════════════════════════════════════════╝"
                )
            elif log_type == "graph_routing":
                # content is expected to be a dict with from_node and to_node
                data = content if isinstance(content, dict) else {}
                output.append(
                    "\n"
                    "╔══════════════════════════════════════════════════════════════╗\n"
                    "║                      GRAPH ROUTING                           ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"║ From: {data.get('from_node', 'N/A'):<52} ║\n"
                    f"║ To:   {data.get('to_node', 'N/A'):<52} ║\n"
                    "╚══════════════════════════════════════════════════════════════╝"
                )
            elif log_type == "approval_request":
                # content is expected to be a dict with reason and verdict
                data = content if isinstance(content, dict) else {}
                output.append(
                    "\n"
                    "╔══════════════════════════════════════════════════════════════╗\n"
                    "║                   APPROVAL REQUEST                           ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"║ Reason: {data.get('reason', 'N/A'):<50} ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    "║ QUESTION                                                     ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"{self._format_box_text(data.get('verdict', 'N/A'))}\n"
                    "╚══════════════════════════════════════════════════════════════╝"
                )
            elif log_type == "approval_decision":
                # content is expected to be a dict with decision and notes
                data = content if isinstance(content, dict) else {}
                output.append(
                    "\n"
                    "╔══════════════════════════════════════════════════════════════╗\n"
                    "║                   APPROVAL DECISION                          ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"║ Decision: {data.get('decision', 'N/A'):<48} ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    "║ NOTES                                                        ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"{self._format_box_text(data.get('notes', 'N/A'))}\n"
                    "╚══════════════════════════════════════════════════════════════╝"
                )
            elif log_type == "interrupt":
                # content is expected to be a dict with reason and data
                data = content if isinstance(content, dict) else {}
                output.append(
                    "\n"
                    "╔══════════════════════════════════════════════════════════════╗\n"
                    "║                     GRAPH INTERRUPT                          ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"║ Reason: {data.get('reason', 'N/A'):<50} ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    "║ DATA                                                         ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"{self._format_box_text_pprint(data.get('data', 'N/A'))}\n"
                    "╚══════════════════════════════════════════════════════════════╝"
                )
            elif log_type == "query_summary":
                # content is expected to be a dict with query stats
                data = content if isinstance(content, dict) else {}
                output.append(
                    "\n"
                    "╔══════════════════════════════════════════════════════════════╗\n"
                    "║                      QUERY SUMMARY                           ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"║ Total LLM Calls: {data.get('llm_calls', 0):<44} ║\n"
                    f"║ Tools Executed: {data.get('tools_executed', 0):<44} ║\n"
                    f"║ Nodes Executed: {data.get('nodes_executed', 0):<44} ║\n"
                    f"║ Total Tokens: {data.get('total_tokens', 'N/A'):<43} ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    "║ FINAL RESPONSE                                               ║\n"
                    "╠══════════════════════════════════════════════════════════════╣\n"
                    f"{self._format_box_text(data.get('final_response', 'N/A'))}\n"
                    "╚══════════════════════════════════════════════════════════════╝"
                )
            else:
                # Custom log
                output.append(f"[{log_type}] {content}")
        
        return "\n".join(output)

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

    @staticmethod
    def _format_box_text(text, width=56):
        if not text:
            return "║ <none>" + " " * 49 + "║"
        return "\n".join(
            f"║ {line:<56} ║"
            for line in wrap(str(text), width=56)
        )

    @staticmethod
    def _format_box_text_pprint(text, width=56):
        if not text:
            return "║ <none>" + " " * 49 + "║"
        formatted = pformat(text, width=width-4)
        return "\n".join(
            f"║ {line:<56} ║"
            for line in wrap(formatted, width=56)
        )

    def log_agent_start(self, query: str, log_capture=None):
        if not self.enabled:
            if log_capture:
                log_capture.add("agent_start", query)
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
        if log_capture:
            log_capture.add("agent_start", query)

    def log_state(self, state, log_capture=None):
        if not self.enabled:
            if log_capture:
                log_capture.add("state", state)
            return
        self.logger.debug(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                      CURRENT STATE                           ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{self._format_box_text_pprint(state)}\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )
        if log_capture:
            log_capture.add("state", state)

    def log_node_execution(self, node_name: str, log_capture=None):
        if not self.enabled:
            if log_capture:
                log_capture.add("node_execution", node_name)
            return
        self.logger.debug(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                      NODE EXECUTION                          ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"║ Node: {node_name:<52} ║\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )
        if log_capture:
            log_capture.add("node_execution", node_name)

    def log_llm_response(self, model, query, response, msg, metadata="N/A", log_capture=None):
        # Prepare data for log capture
        llm_data = {
            'model': model,
            'finish_reason': response.choices[0].finish_reason if hasattr(response, 'choices') and response.choices else 'N/A',
            'query': query,
            'content': msg.content if hasattr(msg, 'content') else 'N/A',
            'tool_calls': msg.tool_calls if hasattr(msg, 'tool_calls') else 'N/A',
            'metadata': metadata
        }
        
        if not self.enabled:
            if log_capture:
                log_capture.add("llm_response", llm_data)
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
        if log_capture:
            log_capture.add("llm_response", llm_data)

    def log_tool_call(self, tool_name: str, arguments: dict, log_capture=None):
        tool_data = {'tool_name': tool_name, 'arguments': arguments}
        if not self.enabled:
            if log_capture:
                log_capture.add("tool_call", tool_data)
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
        if log_capture:
            log_capture.add("tool_call", tool_data)

    def log_tool_result(self, tool_name: str, result, is_error: bool = False, log_capture=None):
        status = "ERROR" if is_error else "SUCCESS"
        tool_data = {'tool_name': tool_name, 'result': result, 'is_error': is_error}
        if not self.enabled:
            if log_capture:
                log_capture.add("tool_result", tool_data)
            return
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
        if log_capture:
            log_capture.add("tool_result", tool_data)

    def log_graph_routing(self, from_node: str, to_node: str, log_capture=None):
        routing_data = {'from_node': from_node, 'to_node': to_node}
        if not self.enabled:
            if log_capture:
                log_capture.add("graph_routing", routing_data)
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
        if log_capture:
            log_capture.add("graph_routing", routing_data)

    def log_approval_request(self, reason: str, verdict: str, log_capture=None):
        approval_data = {'reason': reason, 'verdict': verdict}
        if not self.enabled:
            if log_capture:
                log_capture.add("approval_request", approval_data)
            return
        self.logger.debug(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                   APPROVAL REQUEST                           ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"║ Reason: {reason:<50} ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ QUESTION                                                     ║\n"
            "╠════════════════════════════════════════════════════════════╣\n"
            f"{self._format_box_text(verdict)}\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )
        if log_capture:
            log_capture.add("approval_request", approval_data)

    def log_approval_decision(self, decision: str, notes: str = "", log_capture=None):
        approval_data = {'decision': decision, 'notes': notes}
        if not self.enabled:
            if log_capture:
                log_capture.add("approval_decision", approval_data)
            return
        self.logger.debug(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                   APPROVAL DECISION                          ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"║ Decision: {decision:<48} ║\n"
            "╠════════════════════════════════════════════════════════════╣\n"
            "║ NOTES                                                        ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{self._format_box_text(notes)}\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )
        if log_capture:
            log_capture.add("approval_decision", approval_data)

    def log_message_added(self, role: str, content_preview: str):
        if not self.enabled:
            return
        self.logger.debug(
            f"[MESSAGE ADDED] Role: {role}, Content: {content_preview[:100]}..."
        )

    def log_interrupt(self, reason: str, data, log_capture=None):
        interrupt_data = {'reason': reason, 'data': data}
        if not self.enabled:
            if log_capture:
                log_capture.add("interrupt", interrupt_data)
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
            "╚════════════════════════════════════════════════════════════════╝"
        )
        if log_capture:
            log_capture.add("interrupt", interrupt_data)

    def log_custom(self, message: str, log_capture=None):
        if not self.enabled:
            if log_capture:
                log_capture.add("custom", message)
            return
        self.logger.debug(message)
        if log_capture:
            log_capture.add("custom", message)

    def log_tools_available(self, tools: list, log_capture=None):
        tools_info = f"Total Tools: {len(tools)}, Names: {[tool.name for tool in tools]}"
        if not self.enabled:
            if log_capture:
                log_capture.add("tools_available", tools_info)
            return
        self.logger.debug(
            "\n"
            "╔════════════════════════════════════════════════════════════╗\n"
            "║                    TOOLS AVAILABLE                           ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"║ Total Tools: {len(tools):<48} ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ TOOL NAMES                                                   ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{self._format_box_text_pprint([tool.name for tool in tools])}\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )
        if log_capture:
            log_capture.add("tools_available", tools_info)

    def log_query_summary(self, query: str, stats: dict, show_state: bool = False, log_capture=None):
        final_response = stats.get('final_response', 'N/A')
        if final_response is None:
            final_response = 'No response generated'
        if not self.enabled:
            if log_capture:
                log_capture.add("query_summary", stats)
            return
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
            self.logger.log_state(stats['state'], log_capture)
        if log_capture:
            log_capture.add("query_summary", stats)

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