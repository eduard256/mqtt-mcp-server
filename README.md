# MQTT MCP Server

A Model Context Protocol (MCP) server that enables AI assistants to discover, monitor, and control smart home devices through MQTT.

## Features

- 🔍 **Topic Discovery**: Scan and search MQTT topics with keyword filtering
- 📊 **Value Reading**: Read current values from specific topics with caching
- 📤 **Publishing**: Send commands to MQTT devices with validation
- 📹 **Event Recording**: Monitor MQTT traffic in real-time

## Installation

```bash
# Install from source
pip install -e .

# Or install dependencies directly
pip install mcp aiomqtt pydantic
```

## Configuration

Configure the MQTT connection using environment variables:

```bash
export MQTT_HOST="localhost"      # Default: localhost
export MQTT_PORT="1883"           # Default: 1883
export MQTT_USERNAME="user"       # Optional
export MQTT_PASSWORD="pass"       # Optional
```

## MCP Client Configuration

### Claude Desktop

Add to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mqtt": {
      "command": "python",
      "args": ["-m", "mqtt_mcp.server"],
      "env": {
        "MQTT_HOST": "10.0.20.104",
        "MQTT_PORT": "1883",
        "MQTT_USERNAME": "mqtt",
        "MQTT_PASSWORD": "mqtt"
      }
    }
  }
}
```

### Claude Code

Add to your project settings:

```json
{
  "mcp": {
    "mqtt": {
      "command": "python",
      "args": ["-m", "mqtt_mcp.server"],
      "env": {
        "MQTT_HOST": "localhost",
        "MQTT_PORT": "1883"
      }
    }
  }
}
```

### Cursor / Other MCP Clients

Use the standard MCP configuration format with stdio transport:

```json
{
  "mqtt-server": {
    "transport": "stdio",
    "command": "mqtt-mcp-server",
    "env": {
      "MQTT_HOST": "your-broker-host",
      "MQTT_PORT": "1883"
    }
  }
}
```

## Tools

### 1. topics - Discover MQTT Topics

Scan the MQTT broker to discover active topics.

**Parameters:**
- `scan_timeout` (int, 1-60): How long to scan for topics (default: 10)
- `keywords` (list): Filter topics by keywords (OR logic)
- `limit` (int, 1-200): Maximum results to return (default: 50)
- `offset` (int): Pagination offset (default: 0)

**Example:**
```json
{
  "tool": "topics",
  "arguments": {
    "scan_timeout": 15,
    "keywords": ["temperature", "sensor"],
    "limit": 20
  }
}
```

### 2. value - Read Topic Values

Read current values from specific MQTT topics with caching support.

**Parameters:**
- `topics` (list, required): Topic paths to read
- `timeout` (int, 1-60): Wait time per topic (default: 5)

**Example:**
```json
{
  "tool": "value",
  "arguments": {
    "topics": ["sensor/temperature", "sensor/humidity"],
    "timeout": 10
  }
}
```

### 3. publish - Send Messages

Publish messages to MQTT topics with validation.

**Parameters:**
- `messages` (list, required): Messages to publish
  - `topic` (string, required): Topic to publish to
  - `payload` (any, required): Message payload
  - `qos` (int, 0-2): Quality of Service (default: 1)
  - `retain` (bool): Retain message (default: false)
- `timeout` (int, 1-30): Network timeout (default: 3)

**Example:**
```json
{
  "tool": "publish",
  "arguments": {
    "messages": [
      {
        "topic": "device/light/set",
        "payload": {"state": "ON", "brightness": 80},
        "qos": 1,
        "retain": false
      }
    ]
  }
}
```

### 4. record - Monitor Events

Record MQTT events in real-time for analysis.

**Parameters:**
- `timeout` (int, 1-300): Recording duration (default: 30)
- `topics` (list): Specific topics to monitor
- `keywords` (list): Filter by keywords (OR logic)

**Example:**
```json
{
  "tool": "record",
  "arguments": {
    "timeout": 60,
    "keywords": ["motion", "door"]
  }
}
```

## Cache Management

The server maintains a cache of discovered topics and their last values in `~/.mqtt-mcp-cache.json`. This cache:
- Speeds up topic value reading
- Preserves discovered topics between sessions
- Updates automatically during operations

## Error Handling

All tools provide detailed error messages with suggestions:
- Connection errors include broker details
- Timeout errors suggest using topic discovery
- Validation errors list specific issues

## Logging

All logs are sent to stderr to maintain clean JSON-RPC communication on stdout. Monitor logs with:

```bash
mqtt-mcp-server 2>mqtt.log
```

## Development

```bash
# Clone repository
git clone https://github.com/yourusername/mqtt-mcp-server.git
cd mqtt-mcp-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install in development mode
pip install -e .

# Run tests
python tests/test_topics.py
python tests/test_value.py
python tests/test_publish.py
python tests/test_record.py
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.