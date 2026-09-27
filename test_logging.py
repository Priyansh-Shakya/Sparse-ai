"""
Test script to verify the logging system works correctly.
This demonstrates the logging functionality with logging enabled and disabled.
"""

import asyncio
import sys
sys.path.insert(0, 'E:/priyansh/Agents/MyAgent/src')

from sparse_ai.agent.agent import Agent
from sparse_ai.client.client import Client
from sparse_ai.core.enums import Providers
from sparse_ai.tools.tools import Tool
from sparse_ai.messages.messages import Message


# Sample tool for testing
@Tool
def get_weather(location: str) -> str:
    """
    Get the current weather for a location.

    Args:
        location (str): The city or location to get weather for.

    Returns:
        str: Weather information.
    """
    return f"The weather in {location} is sunny and 75°F."


async def test_logging_enabled():
    """Test agent with logging enabled."""
    print("\n" + "="*80)
    print("TEST 1: Agent with logging=True")
    print("="*80 + "\n")

    # Create client (you'll need to provide a real API key)
    try:
        client = Client(
            api_key="test_key",  # Replace with real key for actual testing
            provider=Providers.GROQ,
            model="llama-3.3-70b-versatile",
            temperature=0
        )

        # Create agent with logging enabled
        agent = Agent(
            client=client,
            messages=[],
            tools=[get_weather],
            logging=True  # Enable logging
        )

        # Run the agent
        # response = await agent.run("What's the weather in San Francisco?")
        # print(f"\nFinal response: {response}")

        print("[OK] Agent created successfully with logging=True")
        print(f"[OK] Logger instance: {agent.logger}")
        print(f"[OK] Logger enabled: {agent.logger.enabled}")
        print(f"[OK] Graph has logger: {agent.graph.logger is not None}")
        print(f"[OK] State has logger: {agent.state.logger is not None}")
        print(f"[OK] Client has logger: {agent.client.logger is not None}")

    except Exception as e:
        print(f"Error (expected without real API key): {e}")


async def test_logging_disabled():
    """Test agent with logging disabled."""
    print("\n" + "="*80)
    print("TEST 2: Agent with logging=False")
    print("="*80 + "\n")

    try:
        client = Client(
            api_key="test_key",
            provider=Providers.GROQ,
            model="llama-3.3-70b-versatile",
            temperature=0
        )

        # Create agent with logging disabled
        agent = Agent(
            client=client,
            messages=[],
            tools=[get_weather],
            logging=False  # Disable logging
        )

        print("[OK] Agent created successfully with logging=False")
        print(f"[OK] Logger instance: {agent.logger}")
        print(f"[OK] Logger enabled: {agent.logger.enabled}")
        print(f"[OK] Graph has logger: {agent.graph.logger is not None}")
        print(f"[OK] State has logger: {agent.state.logger is not None}")
        print(f"[OK] Client has logger: {agent.client.logger is not None}")

    except Exception as e:
        print(f"Error: {e}")


async def test_logger_methods():
    """Test individual logger methods."""
    print("\n" + "="*80)
    print("TEST 3: Testing individual logger methods")
    print("="*80 + "\n")

    from sparse_ai.core.logging import SparseLogger as Logger

    # Test with logging enabled
    logger = Logger(enabled=True)
    print("Testing with logging enabled:")
    logger.log_agent_start("Test query")
    logger.log_state("Test state")
    logger.log_node_execution("test_node")
    logger.log_graph_routing("node_a", "node_b")
    logger.log_tool_call("test_tool", {"arg1": "value1"})
    logger.log_tool_result("test_tool", "result text", is_error=False)
    logger.log_approval_request("Test reason", "Test verdict")
    logger.log_approval_decision("approve", "Test notes")
    logger.log_interrupt("Test interrupt", {"data": "test"})
    logger.log_custom("Custom log message")

    print("\n" + "-"*80 + "\n")

    # Test with logging disabled
    logger_disabled = Logger(enabled=False)
    print("Testing with logging disabled (should produce no output):")
    logger_disabled.log_agent_start("Test query")
    logger_disabled.log_state("Test state")
    logger_disabled.log_node_execution("test_node")
    print("[OK] No output produced as expected")


async def main():
    """Run all tests."""
    # await test_logging_enabled()
    # await test_logging_disabled()
    await test_logger_methods()

    print("\n" + "="*80)
    print("[SUCCESS] All logging tests completed!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
