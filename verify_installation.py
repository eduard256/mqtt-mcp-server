#!/usr/bin/env python3
"""Verify MQTT MCP Server installation."""

import sys
import os

print("=" * 60)
print("MQTT MCP Server - Installation Verification")
print("=" * 60)

# Check Python version
print(f"\n✓ Python version: {sys.version}")

# Check imports
modules_ok = True
try:
    print("\nChecking core modules:")

    from mqtt_mcp import __version__
    print(f"✓ mqtt_mcp v{__version__}")

    from mqtt_mcp.cache import load_cache, save_cache
    print("✓ cache module")

    from mqtt_mcp.mqtt_client import MQTTClient
    print("✓ mqtt_client module")

    from mqtt_mcp.tools.record import record
    print("✓ tools.record")

    from mqtt_mcp.tools.topics import topics
    print("✓ tools.topics")

    from mqtt_mcp.tools.value import value
    print("✓ tools.value")

    from mqtt_mcp.tools.publish import publish
    print("✓ tools.publish")

    from mqtt_mcp.server import server
    print("✓ server module")

except ImportError as e:
    print(f"✗ Import error: {e}")
    modules_ok = False

# Check dependencies
print("\nChecking dependencies:")
try:
    import mcp
    print("✓ mcp")
except ImportError:
    print("✗ mcp not installed")
    modules_ok = False

try:
    import aiomqtt
    print("✓ aiomqtt")
except ImportError:
    print("✗ aiomqtt not installed")
    modules_ok = False

try:
    import pydantic
    print(f"✓ pydantic v{pydantic.VERSION}")
except ImportError:
    print("✗ pydantic not installed")
    modules_ok = False

# Check environment variables
print("\nEnvironment configuration:")
mqtt_host = os.environ.get("MQTT_HOST", "localhost")
mqtt_port = os.environ.get("MQTT_PORT", "1883")
mqtt_user = os.environ.get("MQTT_USERNAME", "")
mqtt_pass = os.environ.get("MQTT_PASSWORD", "")

print(f"  MQTT_HOST: {mqtt_host}")
print(f"  MQTT_PORT: {mqtt_port}")
print(f"  MQTT_USERNAME: {'***' if mqtt_user else '(not set)'}")
print(f"  MQTT_PASSWORD: {'***' if mqtt_pass else '(not set)'}")

# Check tools registration
print("\nChecking tool registration:")
try:
    from mqtt_mcp.server import server
    import asyncio

    async def check_tools():
        tools = await server.list_tools()
        print(f"✓ Registered {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:60]}...")

    asyncio.run(check_tools())
except Exception as e:
    print(f"✗ Error checking tools: {e}")

# Summary
print("\n" + "=" * 60)
if modules_ok:
    print("✅ INSTALLATION SUCCESSFUL!")
    print("\nTo run the server:")
    print("  python -m mqtt_mcp.server")
    print("\nOr with the installed command:")
    print("  mqtt-mcp-server")
else:
    print("❌ INSTALLATION INCOMPLETE")
    print("Please check the errors above.")

print("=" * 60)