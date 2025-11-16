"""MQTT MCP Server - Main entry point."""

import asyncio
import signal
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import ValidationError

from .tools.record import record, RecordParams
from .tools.topics import topics, TopicsParams
from .tools.value import value, ValueParams
from .tools.publish import publish, PublishParams, PublishMessage
from .cache import save_cache


# Create server instance
server = Server(name="mqtt-mcp-server", version="1.0.1")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MQTT tools."""
    return [
        Tool(
            name="topics",
            description="Discover and search MQTT topics with filtering and pagination",
            inputSchema={
                "type": "object",
                "properties": {
                    "scan_timeout": {
                        "type": "integer",
                        "description": "How long to scan for topics (1-60 seconds)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 60
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords to filter topics (OR logic)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 200
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Pagination offset",
                        "default": 0,
                        "minimum": 0
                    }
                }
            }
        ),
        Tool(
            name="value",
            description="Read current values from specific MQTT topics with caching",
            inputSchema={
                "type": "object",
                "properties": {
                    "topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Topic paths to read",
                        "minItems": 1
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Wait time per topic in seconds",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 60
                    }
                },
                "required": ["topics"]
            }
        ),
        Tool(
            name="publish",
            description="Publish messages to MQTT topics with validation",
            inputSchema={
                "type": "object",
                "properties": {
                    "messages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "topic": {
                                    "type": "string",
                                    "description": "Topic to publish to",
                                    "minLength": 1
                                },
                                "payload": {
                                    "description": "Payload to publish (any JSON-serializable type)"
                                },
                                "qos": {
                                    "type": "integer",
                                    "description": "Quality of Service level",
                                    "default": 1,
                                    "minimum": 0,
                                    "maximum": 2
                                },
                                "retain": {
                                    "type": "boolean",
                                    "description": "Retain message on broker",
                                    "default": False
                                }
                            },
                            "required": ["topic", "payload"]
                        },
                        "description": "Messages to publish",
                        "minItems": 1
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Network timeout in seconds",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 30
                    }
                },
                "required": ["messages"]
            }
        ),
        Tool(
            name="record",
            description="Record MQTT events in real-time for discovering device behaviors",
            inputSchema={
                "type": "object",
                "properties": {
                    "timeout": {
                        "type": "integer",
                        "description": "Recording duration in seconds",
                        "default": 30,
                        "minimum": 1,
                        "maximum": 300
                    },
                    "topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific topics to subscribe to"
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords to filter topics (OR logic)"
                    }
                }
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Execute MQTT tool."""
    try:
        if name == "topics":
            params = TopicsParams(**arguments)
            result = await topics(params)

        elif name == "value":
            params = ValueParams(**arguments)
            result = await value(params)

        elif name == "publish":
            # Handle nested message objects
            messages = []
            for msg in arguments.get("messages", []):
                messages.append(PublishMessage(**msg))
            params = PublishParams(
                messages=messages,
                timeout=arguments.get("timeout", 3)
            )
            result = await publish(params)

        elif name == "record":
            params = RecordParams(**arguments)
            result = await record(params)

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

        # Return result as JSON string
        import json
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False)
        )]

    except ValidationError as e:
        # Return validation errors
        errors = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            errors.append(f"{field}: {error['msg']}")

        return [TextContent(
            type="text",
            text=f"Validation error:\n" + "\n".join(errors)
        )]

    except Exception as e:
        # Return other errors
        sys.stderr.write(f"Tool execution error: {e}\n")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def main():
    """Main server entry point."""
    sys.stderr.write("Starting MQTT MCP Server v1.0.1\n")
    sys.stderr.write("All output goes to stderr. stdout is reserved for JSON-RPC.\n")

    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        sys.stderr.write("\nShutdown signal received, saving cache...\n")
        save_cache()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run server using stdio transport
    from mcp.server.models import InitializationOptions
    from mcp.types import ServerCapabilities

    async with stdio_server() as (stdin, stdout):
        init_options = InitializationOptions(
            server_name="mqtt-mcp-server",
            server_version="1.0.1",
            capabilities=ServerCapabilities(
                tools={}
            )
        )
        await server.run(stdin, stdout, init_options)


if __name__ == "__main__":
    asyncio.run(main())