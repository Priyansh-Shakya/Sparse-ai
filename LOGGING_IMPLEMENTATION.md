# Logging System Implementation

## Overview
Successfully implemented a comprehensive logging system for the agent framework that allows users to control when and when not agent.run(query) shows logs and only output.

## Changes Made

### 1. Enhanced SparseLogger Class (`src/sparse_ai/core/logging.py`)
- Converted from static methods to instance-based logging
- Added `enabled` parameter to control logging on/off
- Created beautiful structured logging with boxed display formats using `textwrap` and `pprint`
- Added specific logging methods for different events:
  - `log_agent_start()` - Logs when agent execution begins
  - `log_state()` - Logs current state information
  - `log_node_execution()` - Logs when a node is executed
  - `log_llm_response()` - Logs LLM responses with detailed information
  - `log_tool_call()` - Logs tool calls with arguments
  - `log_tool_result()` - Logs tool execution results
  - `log_graph_routing()` - Logs graph routing decisions
  - `log_approval_request()` - Logs approval requests
  - `log_approval_decision()` - Logs approval decisions
  - `log_interrupt()` - Logs graph interrupts
  - `log_custom()` - For custom log messages

### 2. Updated Agent Class (`src/sparse_ai/agent/agent.py`)
- Added `logging: bool = True` parameter to `__init__()`
- Creates `SparseLogger` instance based on logging parameter
- Passes logger instance to all components:
  - Graph
  - State
  - Client
  - Client's adapter
- Replaced print statements with structured logging calls
- Updated docstrings to document the logging parameter

### 3. Updated Graph Class (`src/sparse_ai/graph/graph/graph.py`)
- Added `logger` attribute to store logger instance
- Modified `compile()` method to accept and store logger
- Added logging in `_resolve_next()` for graph routing
- Added logging in `run()` for node execution
- Added logging in `_build_llm_node()` for tool call detection
- Added logging in `_build_tool_node()` for tool execution and results

### 4. Updated State Class (`src/sparse_ai/state/state.py`)
- Added `logger` attribute to store logger instance
- Modified `__setitem__()` to log state changes when logger is enabled

### 5. Updated Client Class (`src/sparse_ai/client/client.py`)
- Added `logger` attribute to store logger instance
- Added `stream_enabled` attribute for stream control

### 6. Updated Adapters (`src/sparse_ai/client/adapters.py`)
- Removed static logger import
- Added `logger` attribute to all adapter classes:
  - `OpenAICompatibleAdapter`
  - `GeminiAdapter`
  - `ClaudeAdapter`
- Replaced print statements with conditional logging
- Updated LLM response logging to use instance logger

### 7. Updated Tools (`src/sparse_ai/tools/tools.py`)
- Removed print statements from tool execution
- Tool execution logging is now handled by the graph/node layer

### 8. Updated Approval Nodes (`src/sparse_ai/graph/nodes/special_nodes.py`)
- Added logging for approval requests
- Added logging for approval decisions
- Uses state.logger instance

## Usage

### Enable Logging (Default)
```python
agent = Agent(
    client=client,
    messages=[],
    tools=[my_tool],
    logging=True  # Shows detailed logs
)
response = await agent.run("What's the weather?")
```

### Disable Logging
```python
agent = Agent(
    client=client,
    messages=[],
    tools=[my_tool],
    logging=False  # Only shows final output
)
response = await agent.run("What's the weather?")
```

## Log Output Examples

When logging is enabled, you'll see beautiful structured output like:

```
╔══════════════════════════════════════════════════════════════╗
║                    AGENT EXECUTION START                     ║
╠══════════════════════════════════════════════════════════════╣
║ USER QUERY                                                   ║
╠══════════════════════════════════════════════════════════════╣
║ What's the weather in San Francisco?                       ║
╚══════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════╗
║                      NODE EXECUTION                          ║
╠══════════════════════════════════════════════════════════════╣
║ Node: llm_call                                               ║
╚══════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════╗
║                      GRAPH ROUTING                           ║
╠══════════════════════════════════════════════════════════════╣
║ From: llm_call                                               ║
║ To:   tool_exec                                              ║
╚══════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════╗
║                       TOOL CALL                              ║
╠══════════════════════════════════════════════════════════════╣
║ Tool: get_weather                                            ║
╠══════════════════════════════════════════════════════════════╣
║ ARGUMENTS                                                    ║
╠══════════════════════════════════════════════════════════════╣
║ {'location': 'San Francisco'}                               ║
╚══════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════╗
║                      TOOL RESULT                            ║
╠══════════════════════════════════════════════════════════════╣
║ Tool: get_weather                                            ║
║ Status: SUCCESS                                              ║
╠══════════════════════════════════════════════════════════════╣
║ RESULT                                                       ║
╠══════════════════════════════════════════════════════════════╣
║ The weather in San Francisco is sunny and 75°F.           ║
╚══════════════════════════════════════════════════════════════╝
```

## Benefits

1. **Controlled Logging**: Users can easily toggle logging on/off with a single parameter
2. **Beautiful Output**: Structured, boxed displays make logs easy to read
3. **Comprehensive Coverage**: Logs all major events in the agent lifecycle
4. **No Performance Impact**: When disabled, logging calls return immediately
5. **Consistent Interface**: Single logger instance propagated throughout the framework
6. **Debugging Support**: Detailed logs help understand agent behavior
7. **Production Ready**: Can disable logs in production for clean output

## Testing

A test script (`test_logging.py`) was created to verify:
- Logger instance creation with enabled/disabled states
- Logger propagation to all components
- Individual logging method functionality
- Logging control (enabled shows output, disabled doesn't)

The test successfully demonstrates that:
- Logging works when enabled
- No output is produced when disabled
- All components receive the logger instance
- Beautiful structured output is generated
