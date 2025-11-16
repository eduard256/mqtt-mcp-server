# MQTT MCP Server

[![PyPI version](https://badge.fury.io/py/mqtt-mcp-server.svg)](https://badge.fury.io/py/mqtt-mcp-server)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server that enables AI assistants to discover, monitor, and control smart home devices through MQTT.

## Features

- 🔍 **Topic Discovery**: Scan and search MQTT topics with keyword filtering
- 📊 **Value Reading**: Read current values from specific topics with caching
- 📤 **Publishing**: Send commands to MQTT devices with validation
- 📹 **Event Recording**: Monitor MQTT traffic in real-time

## Quick Start

### Installation

Install from PyPI:

```bash
pip install mqtt-mcp-server
```

Or install from source:

```bash
git clone https://github.com/eduard256/mqtt-mcp-server.git
cd mqtt-mcp-server
pip install -e .
```

### Requirements

- Python 3.10 or higher
- MQTT broker (e.g., Mosquitto, HiveMQ, EMQX)

## Configuration

The server uses environment variables for MQTT broker configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| `MQTT_HOST` | MQTT broker hostname or IP | `localhost` |
| `MQTT_PORT` | MQTT broker port | `1883` |
| `MQTT_USERNAME` | MQTT username (optional) | - |
| `MQTT_PASSWORD` | MQTT password (optional) | - |

## Setup for Different MCP Clients

### Claude Desktop

**Step 1**: Install the package

```bash
pip install mqtt-mcp-server
```

**Step 2**: Configure Claude Desktop

Edit the configuration file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the MQTT server configuration:

```json
{
  "mcpServers": {
    "mqtt": {
      "command": "python3",
      "args": ["-m", "mqtt_mcp.server"],
      "env": {
        "MQTT_HOST": "your-broker-host",
        "MQTT_PORT": "1883",
        "MQTT_USERNAME": "your-username",
        "MQTT_PASSWORD": "your-password"
      }
    }
  }
}
```

**Windows users**: Use `python` instead of `python3`

**Step 3**: Restart Claude Desktop

The MQTT tools will now be available in Claude Desktop.

---

### Using Command Line

**Linux / macOS:**

```bash
# Install
pip install mqtt-mcp-server

# Add to your project
claude mcp add --transport stdio mqtt \
  --env MQTT_HOST=your-broker \
  --env MQTT_PORT=1883 \
  --env MQTT_USERNAME=username \
  --env MQTT_PASSWORD=password \
  -- python3 -m mqtt_mcp.server
```

**Windows:**

```powershell
# Install
pip install mqtt-mcp-server

# Add to your project
claude mcp add --transport stdio mqtt `
  --env MQTT_HOST=your-broker `
  --env MQTT_PORT=1883 `
  --env MQTT_USERNAME=username `
  --env MQTT_PASSWORD=password `
  -- python -m mqtt_mcp.server
```

---

### Cursor

**Step 1**: Install the package

```bash
pip install mqtt-mcp-server
```

**Step 2**: Configure Cursor

Add to your Cursor settings (`.cursor/mcp.json` or global settings):

```json
{
  "mcpServers": {
    "mqtt": {
      "type": "stdio",
      "command": "python3",
      "args": ["-m", "mqtt_mcp.server"],
      "env": {
        "MQTT_HOST": "your-broker-host",
        "MQTT_PORT": "1883",
        "MQTT_USERNAME": "your-username",
        "MQTT_PASSWORD": "your-password"
      }
    }
  }
}
```

**Windows users**: Replace `python3` with `python`

---

### Cline (VS Code Extension)

**Step 1**: Install the package

```bash
pip install mqtt-mcp-server
```

**Step 2**: Configure Cline

Add to Cline MCP settings:

```json
{
  "mcpServers": {
    "mqtt": {
      "command": "python3",
      "args": ["-m", "mqtt_mcp.server"],
      "env": {
        "MQTT_HOST": "your-broker-host",
        "MQTT_PORT": "1883",
        "MQTT_USERNAME": "your-username",
        "MQTT_PASSWORD": "your-password"
      }
    }
  }
}
```

---

### Verification

After configuration, verify the server is working:

**For Command Line users:**

```bash
claude mcp list
```

You should see:
```
mqtt: python3 -m mqtt_mcp.server - ✓ Connected
```

**For Desktop/GUI clients:**

Ask your AI assistant: "What MQTT tools are available?"

The assistant should list: `topics`, `value`, `publish`, and `record` tools.

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

### Linux / macOS

```bash
# Clone repository
git clone https://github.com/eduard256/mqtt-mcp-server.git
cd mqtt-mcp-server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .

# Run tests
python3 tests/test_topics.py
python3 tests/test_value.py
python3 tests/test_publish.py
python3 tests/test_record.py
```

### Windows

```powershell
# Clone repository
git clone https://github.com/eduard256/mqtt-mcp-server.git
cd mqtt-mcp-server

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install in development mode
pip install -e .

# Run tests
python tests\test_topics.py
python tests\test_value.py
python tests\test_publish.py
python tests\test_record.py
```

## Troubleshooting

### Common Issues

**"python3 not found" on Windows**
- Use `python` instead of `python3` in all commands

**"Connection refused" error**
- Check if your MQTT broker is running
- Verify `MQTT_HOST` and `MQTT_PORT` are correct
- Check firewall settings

**"ModuleNotFoundError: No module named 'mqtt_mcp'"**
- Make sure you installed the package: `pip install mqtt-mcp-server`
- If using virtual environment, make sure it's activated

**Tools not showing up in Claude/Cursor**
- Restart the application after configuration
- Check configuration file syntax (valid JSON)
- Verify the server connects: `claude mcp list`

## License

MIT License - see [LICENSE](LICENSE) file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Links

- **PyPI**: https://pypi.org/project/mqtt-mcp-server/
- **GitHub**: https://github.com/eduard256/mqtt-mcp-server
- **Issues**: https://github.com/eduard256/mqtt-mcp-server/issues

## Author

Eduard Kazantsev ([@eduard256](https://github.com/eduard256))