#!/usr/bin/env python3
"""Test the MQTT MCP server with a simple client."""

import asyncio
import json
import sys
import os

# Set environment variables
os.environ["MQTT_HOST"] = "10.0.20.104"
os.environ["MQTT_PORT"] = "1883"
os.environ["MQTT_USERNAME"] = "mqtt"
os.environ["MQTT_PASSWORD"] = "mqtt"

async def test_server():
    """Test basic server functionality."""
    from mcp.client import ClientSession
    from mcp.client.stdio import stdio_client

    print("Testing MQTT MCP Server...", file=sys.stderr)

    # Start the server process
    server_cmd = [sys.executable, "-m", "mqtt_mcp.server"]

    async with stdio_client(server_cmd) as (stdin, stdout):
        session = ClientSession(stdin, stdout)

        # Initialize connection
        await session.initialize()
        print("✓ Server initialized", file=sys.stderr)

        # List tools
        tools = await session.list_tools()
        print(f"✓ Found {len(tools.tools)} tools:", file=sys.stderr)
        for tool in tools.tools:
            print(f"  - {tool.name}: {tool.description[:50]}...", file=sys.stderr)

        # Test topics tool
        print("\nTesting topics tool...", file=sys.stderr)
        result = await session.call_tool(
            "topics",
            {"scan_timeout": 2, "limit": 5}
        )
        data = json.loads(result.content[0].text)
        print(f"✓ Discovered {data.get('total', 0)} topics", file=sys.stderr)

        print("\n✅ All tests passed!", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(test_server())