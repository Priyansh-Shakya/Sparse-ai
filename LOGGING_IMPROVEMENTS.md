# Logging System Improvements

## Summary of Changes

All requested improvements have been implemented to enhance the logging system:

### 1. Changed Default Logging to False ✅
- **File**: `src/sparse_ai/agent/agent.py`
- **Change**: `logging: bool = False` (was `True`)
- **Impact**: Agent now runs without logs by default, showing only final output

### 2. Removed Blind Print Statements ✅
- **File**: `src/sparse_ai/agent/agent.py`
- **Change**: Removed `print(f"Data: {response.data}")` from interrupt handling
- **Impact**: Cleaner output, less noise during execution

### 3. Fixed Tools Logging ✅
- **Files**: `src/sparse_ai/core/logging.py`, `src/sparse_ai/agent/agent.py`, `src/sparse_ai/client/adapters.py`
- **Changes**:
  - Added `log_tools_available()` method to show tools once per query
  - Moved tools logging from adapter `generate()` to agent `run()`
  - Removed redundant tool serialization logging from adapters
- **Impact**: Tools are now shown once at the start of each query, not on every LLM call

### 4. Added Logging to Stream Function ✅
- **File**: `src/sparse_ai/client/adapters.py`
- **Changes**:
  - Added logging to `OpenAICompatibleAdapter.stream()`
  - Logs stream start/completion and token counts
- **Impact**: Streaming operations now have visibility when logging is enabled

### 5. Implemented Stream for Gemini and Claude Adapters ✅
- **File**: `src/sparse_ai/client/adapters.py`
- **Changes**:
  - Added `stream()` method to `GeminiAdapter`
  - Added `stream()` method to `ClaudeAdapter`
  - Both methods compatible with existing streaming infrastructure
  - Include logging support
- **Impact**: All major providers now support streaming with consistent interface

### 6. Added Final Summary Log with Query-Level Statistics ✅
- **Files**: `src/sparse_ai/core/logging.py`, `src/sparse_ai/agent/agent.py`, `src/sparse_ai/graph/graph/graph.py`
- **Changes**:
  - Added `log_query_summary()` method with query-level statistics
  - Added `query_stats` dictionary to track per-query metrics:
    - `llm_calls`: Number of LLM calls per query
    - `tools_executed`: Number of tools executed per query
    - `nodes_executed`: Number of nodes executed per query
    - `total_tokens`: Total tokens used per query
    - `final_response`: Final response text
    - `state`: Full state object (optional display)
  - Integrated statistics tracking in graph execution and tool/LLM nodes
  - Added optional `show_state` parameter to display full state
- **Impact**: Comprehensive query-level visibility with optional state inspection

### 7. Suppressed HTTP Library Logs ✅
- **File**: `src/sparse_ai/core/logging.py`
- **Changes**:
  - Added suppression for `httpcore2` logs
  - Applied suppression even when logging is disabled
- **Impact**: No more verbose HTTP connection logs when logging is disabled

## New Logging Methods

### SparseLogger Enhancements
```python
# Show available tools once per query
logger.log_tools_available(tools_list)

# Show query-level summary with statistics
logger.log_query_summary(query, stats_dict, show_state=False)
```

## Usage Examples

### Default (No Logs)
```python
agent = Agent(client=client, messages=[], tools=[my_tool])
response = await agent.run("What's the weather?")
# Only shows final response, no debug logs
```

### Enable Logging
```python
agent = Agent(client=client, messages=[], tools=[my_tool], logging=True)
response = await agent.run("What's the weather?")
# Shows: agent start, tools available, state, node execution, LLM responses,
# tool calls, routing, and final query summary
```

### Query Summary Output Example
```
╔══════════════════════════════════════════════════════════════╗
║                      QUERY SUMMARY                           ║
╠══════════════════════════════════════════════════════════════╣
║ Total LLM Calls: 3                                        ║
║ Tools Executed: 2                                         ║
║ Nodes Executed: 5                                         ║
║ Total Tokens: 1245                                        ║
╠══════════════════════════════════════════════════════════════╣
║ FINAL RESPONSE                                               ║
╠══════════════════════════════════════════════════════════════╣
║ The weather in San Francisco is sunny and 75°F.           ║
╚══════════════════════════════════════════════════════════════╝
```

## Streaming Support

All adapters now support streaming:
- **OpenAICompatibleAdapter** (OpenAI, Groq, OpenRouter, HuggingFace)
- **GeminiAdapter** (Newly implemented)
- **ClaudeAdapter** (Newly implemented)

Streaming includes:
- Token-by-token yield
- Tool call streaming support
- Logging integration
- Compatible with existing `StreamChunk` interface

## Statistics Tracking

Per-query statistics are tracked separately from global client statistics:
- **Client-level**: Total calls across all queries (existing)
- **Query-level**: Calls for specific query (new)

This allows granular visibility into individual query performance while maintaining overall usage tracking.

## Optional State Display

To enable full state display in query summary:
```python
# In agent.py
self.logger.log_query_summary(query, self.query_stats, show_state=True)
```

This shows the complete state object at the end of each query for debugging purposes.
