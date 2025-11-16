# MQTT MCP Server

[![PyPI](https://badge.fury.io/py/mqtt-mcp-server.svg)](https://badge.fury.io/py/mqtt-mcp-server)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MCP server that connects AI assistants to MQTT brokers for smart home automation and IoT device control.

**What it does:**
- Discovers MQTT topics and devices on your network
- Reads sensor values and device states
- Sends commands to control devices
- Monitors real-time MQTT events

**Use cases:**
- Control smart home devices through AI assistants
- Monitor IoT sensor networks
- Automate home automation workflows
- Debug MQTT integrations

---

## Quick Navigation

**Choose your system:**

### Linux
- [Claude Code](#linux--claude-code) ⭐ Recommended
- [Codex CLI](#linux--codex-cli)
- [Cursor](#linux--cursor)
- [Cline](#linux--cline)
- [Other Clients](#linux--other-clients)

### macOS
- [Claude Code](#macos--claude-code)
- [Codex CLI](#macos--codex-cli)
- [Claude Desktop](#macos--claude-desktop)
- [Cursor](#macos--cursor)
- [Cline](#macos--cline)
- [Other Clients](#macos--other-clients)

### Windows
- [Claude Code](#windows--claude-code)
- [Codex CLI](#windows--codex-cli)
- [Claude Desktop](#windows--claude-desktop)
- [Cursor](#windows--cursor)
- [Cline](#windows--cline)
- [Other Clients](#windows--other-clients)

---

## Linux

### Linux • Claude Code

**Step 1: Install the package**

```bash
pip install mqtt-mcp-server
```

**Step 2: Add to Claude Code**

```bash
claude mcp add --transport stdio mqtt \
  --env MQTT_HOST=YOUR_BROKER_IP \
  --env MQTT_PORT=1883 \
  --env MQTT_USERNAME=YOUR_USERNAME \
  --env MQTT_PASSWORD=YOUR_PASSWORD \
  -- python3 -m mqtt_mcp.server
```

**Step 3: Verify**

```bash
claude mcp list
```

You should see: `mqtt: python3 -m mqtt_mcp.server - ✓ Connected`

---

### Linux • Codex CLI

**Step 1: Install the package**

```bash
pip install mqtt-mcp-server
```

**Step 2: Add to Codex**

```bash
codex mcp add mqtt \
  --env MQTT_HOST=YOUR_BROKER_IP \
  --env MQTT_PORT=1883 \
  --env MQTT_USERNAME=YOUR_USERNAME \
  --env MQTT_PASSWORD=YOUR_PASSWORD \
  -- python3 -m mqtt_mcp.server
```

**Step 3: Verify**

```bash
codex mcp list
```

---

### Linux • Cursor

**Step 1: Install the package**

```bash
pip install mqtt-mcp-server
```

**Step 2: Add to Cursor**

Open Cursor Settings → MCP, or create `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project-only):

```json
{
  "mcpServers": {
    "mqtt": {
      "command": "python3",
      "args": ["-m", "mqtt_mcp.server"],
      "env": {
        "MQTT_HOST": "YOUR_BROKER_IP",
        "MQTT_PORT": "1883",
        "MQTT_USERNAME": "YOUR_USERNAME",
        "MQTT_PASSWORD": "YOUR_PASSWORD"
      }
    }
  }
}
```

**Step 3: Restart Cursor**

---

### Linux • Cline

**Step 1: Install the package**

```bash
pip install mqtt-mcp-server
```

**Step 2: Add to Cline**

In VS Code, click MCP Servers icon → Configure MCP Servers, or edit `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "mqtt": {
      "command": "python3",
      "args": ["-m", "mqtt_mcp.server"],
      "env": {
        "MQTT_HOST": "YOUR_BROKER_IP",
        "MQTT_PORT": "1883",
        "MQTT_USERNAME": "YOUR_USERNAME",
        "MQTT_PASSWORD": "YOUR_PASSWORD"
      }
    }
  }
}
```

**Step 3: Restart VS Code**

---

### Linux • Other Clients

For any MCP client that supports stdio transport:

**1. Install the package:**
```bash
pip install mqtt-mcp-server
```

**2. Configure with these values:**
- **Command:** `python3`
- **Args:** `["-m", "mqtt_mcp.server"]`
- **Environment variables:**
  - `MQTT_HOST` - Your broker IP/hostname
  - `MQTT_PORT` - Broker port (usually 1883)
  - `MQTT_USERNAME` - Optional username
  - `MQTT_PASSWORD` - Optional password

---

## macOS

### macOS • Claude Code

**Step 1: Install the package**

```bash
pip3 install mqtt-mcp-server
```

**Step 2: Add to Claude Code**

```bash
claude mcp add --transport stdio mqtt \
  --env MQTT_HOST=YOUR_BROKER_IP \
  --env MQTT_PORT=1883 \
  --env MQTT_USERNAME=YOUR_USERNAME \
  --env MQTT_PASSWORD=YOUR_PASSWORD \
  -- python3 -m mqtt_mcp.server
```

**Step 3: Verify**

```bash
claude mcp list
```

You should see: `mqtt: python3 -m mqtt_mcp.server - ✓ Connected`

---

### macOS • Codex CLI

**Step 1: Install the package**

```bash
pip3 install mqtt-mcp-server
```

**Step 2: Add to Codex**

```bash
codex mcp add mqtt \
  --env MQTT_HOST=YOUR_BROKER_IP \
  --env MQTT_PORT=1883 \
  --env MQTT_USERNAME=YOUR_USERNAME \
  --env MQTT_PASSWORD=YOUR_PASSWORD \
  -- python3 -m mqtt_mcp.server
```

**Step 3: Verify**

```bash
codex mcp list
```

---

### macOS • Claude Desktop

**Step 1: Install the package**

```bash
pip3 install mqtt-mcp-server
```

**Step 2: Configure Claude Desktop**

Open: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mqtt": {
      "command": "python3",
      "args": ["-m", "mqtt_mcp.server"],
      "env": {
        "MQTT_HOST": "YOUR_BROKER_IP",
        "MQTT_PORT": "1883",
        "MQTT_USERNAME": "YOUR_USERNAME",
        "MQTT_PASSWORD": "YOUR_PASSWORD"
      }
    }
  }
}
```

**Step 3: Restart Claude Desktop**

---

### macOS • Cursor

**Step 1: Install the package**

```bash
pip3 install mqtt-mcp-server
```

**Step 2: Add to Cursor**

Open Cursor Settings → MCP, or create `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project-only):

```json
{
  "mcpServers": {
    "mqtt": {
      "command": "python3",
      "args": ["-m", "mqtt_mcp.server"],
      "env": {
        "MQTT_HOST": "YOUR_BROKER_IP",
        "MQTT_PORT": "1883",
        "MQTT_USERNAME": "YOUR_USERNAME",
        "MQTT_PASSWORD": "YOUR_PASSWORD"
      }
    }
  }
}
```

**Step 3: Restart Cursor**

---

### macOS • Cline

**Step 1: Install the package**

```bash
pip3 install mqtt-mcp-server
```

**Step 2: Add to Cline**

In VS Code, click MCP Servers icon → Configure MCP Servers, or edit `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "mqtt": {
      "command": "python3",
      "args": ["-m", "mqtt_mcp.server"],
      "env": {
        "MQTT_HOST": "YOUR_BROKER_IP",
        "MQTT_PORT": "1883",
        "MQTT_USERNAME": "YOUR_USERNAME",
        "MQTT_PASSWORD": "YOUR_PASSWORD"
      }
    }
  }
}
```

**Step 3: Restart VS Code**

---

### macOS • Other Clients

For any MCP client that supports stdio transport:

**1. Install the package:**
```bash
pip3 install mqtt-mcp-server
```

**2. Configure with these values:**
- **Command:** `python3`
- **Args:** `["-m", "mqtt_mcp.server"]`
- **Environment variables:**
  - `MQTT_HOST` - Your broker IP/hostname
  - `MQTT_PORT` - Broker port (usually 1883)
  - `MQTT_USERNAME` - Optional username
  - `MQTT_PASSWORD` - Optional password

---

## Windows

### Windows • Claude Code

**Step 1: Install the package**

```powershell
pip install mqtt-mcp-server
```

**Step 2: Add to Claude Code**

```powershell
claude mcp add --transport stdio mqtt `
  --env MQTT_HOST=YOUR_BROKER_IP `
  --env MQTT_PORT=1883 `
  --env MQTT_USERNAME=YOUR_USERNAME `
  --env MQTT_PASSWORD=YOUR_PASSWORD `
  -- python -m mqtt_mcp.server
```

**Step 3: Verify**

```powershell
claude mcp list
```

You should see: `mqtt: python -m mqtt_mcp.server - ✓ Connected`

---

### Windows • Codex CLI

**Step 1: Install the package**

```powershell
pip install mqtt-mcp-server
```

**Step 2: Add to Codex**

```powershell
codex mcp add mqtt `
  --env MQTT_HOST=YOUR_BROKER_IP `
  --env MQTT_PORT=1883 `
  --env MQTT_USERNAME=YOUR_USERNAME `
  --env MQTT_PASSWORD=YOUR_PASSWORD `
  -- python -m mqtt_mcp.server
```

**Step 3: Verify**

```powershell
codex mcp list
```

---

### Windows • Claude Desktop

**Step 1: Install the package**

```powershell
pip install mqtt-mcp-server
```

**Step 2: Configure Claude Desktop**

Open: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mqtt": {
      "command": "python",
      "args": ["-m", "mqtt_mcp.server"],
      "env": {
        "MQTT_HOST": "YOUR_BROKER_IP",
        "MQTT_PORT": "1883",
        "MQTT_USERNAME": "YOUR_USERNAME",
        "MQTT_PASSWORD": "YOUR_PASSWORD"
      }
    }
  }
}
```

**Step 3: Restart Claude Desktop**

---

### Windows • Cursor

**Step 1: Install the package**

```powershell
pip install mqtt-mcp-server
```

**Step 2: Add to Cursor**

Open Cursor Settings → MCP, or create `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project-only):

```json
{
  "mcpServers": {
    "mqtt": {
      "command": "python",
      "args": ["-m", "mqtt_mcp.server"],
      "env": {
        "MQTT_HOST": "YOUR_BROKER_IP",
        "MQTT_PORT": "1883",
        "MQTT_USERNAME": "YOUR_USERNAME",
        "MQTT_PASSWORD": "YOUR_PASSWORD"
      }
    }
  }
}
```

**Step 3: Restart Cursor**

---

### Windows • Cline

**Step 1: Install the package**

```powershell
pip install mqtt-mcp-server
```

**Step 2: Add to Cline**

In VS Code, click MCP Servers icon → Configure MCP Servers, or edit `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "mqtt": {
      "command": "python",
      "args": ["-m", "mqtt_mcp.server"],
      "env": {
        "MQTT_HOST": "YOUR_BROKER_IP",
        "MQTT_PORT": "1883",
        "MQTT_USERNAME": "YOUR_USERNAME",
        "MQTT_PASSWORD": "YOUR_PASSWORD"
      }
    }
  }
}
```

**Step 3: Restart VS Code**

---

### Windows • Other Clients

For any MCP client that supports stdio transport:

**1. Install the package:**
```powershell
pip install mqtt-mcp-server
```

**2. Configure with these values:**
- **Command:** `python` (not `python3`)
- **Args:** `["-m", "mqtt_mcp.server"]`
- **Environment variables:**
  - `MQTT_HOST` - Your broker IP/hostname
  - `MQTT_PORT` - Broker port (usually 1883)
  - `MQTT_USERNAME` - Optional username
  - `MQTT_PASSWORD` - Optional password

---

## Available Tools

After installation, ask your AI assistant: **"What MQTT tools are available?"**

You should see 4 tools:

### `topics`
Discover MQTT topics on your broker.
```
Parameters:
- scan_timeout: Scan duration in seconds (1-60, default: 10)
- keywords: Filter topics by keywords
- limit: Max results (1-200, default: 50)
```

### `value`
Read current values from topics (uses cache for speed).
```
Parameters:
- topics: List of topic paths (required)
- timeout: Wait time per topic (1-60, default: 5)
```

### `publish`
Send commands to MQTT devices.
```
Parameters:
- messages: List of {topic, payload, qos, retain}
- timeout: Network timeout (1-30, default: 3)
```

### `record`
Monitor MQTT events in real-time.
```
Parameters:
- timeout: Recording duration (1-300, default: 30)
- topics: Specific topics to monitor
- keywords: Filter by keywords
```

---

## Troubleshooting

**"python3 not found" (Windows)**
```
Use 'python' instead of 'python3' in all commands
```

**"Connection refused"**
```
1. Check MQTT broker is running
2. Verify MQTT_HOST and MQTT_PORT are correct
3. Check firewall settings
4. Test connection: mosquitto_sub -h YOUR_HOST -p 1883 -t "#"
```

**"Module not found: mqtt_mcp"**
```
Install the package: pip install mqtt-mcp-server
If using venv, make sure it's activated
```

**Tools not appearing**
```
1. Restart your AI client
2. Check JSON syntax in config file
3. Verify connection: claude mcp list (or codex mcp list)
4. Check logs (location depends on client)
```

**Permission errors (Linux/macOS)**
```
Use pip3 install --user mqtt-mcp-server
Or install in virtual environment
```

---

## Development

**For contributors and developers:**

### Install from source

```bash
# Clone repository
git clone https://github.com/eduard256/mqtt-mcp-server.git
cd mqtt-mcp-server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

### Run tests

```bash
# Linux/macOS
python3 tests/test_topics.py
python3 tests/test_value.py
python3 tests/test_publish.py
python3 tests/test_record.py

# Windows
python tests\test_topics.py
python tests\test_value.py
python tests\test_publish.py
python tests\test_record.py
```

### Requirements

- Python 3.10+
- MQTT broker (Mosquitto, EMQX, HiveMQ, etc.)

---

## Links

- **PyPI**: https://pypi.org/project/mqtt-mcp-server/
- **GitHub**: https://github.com/eduard256/mqtt-mcp-server
- **Issues**: https://github.com/eduard256/mqtt-mcp-server/issues

## License

MIT License - See [LICENSE](LICENSE) for details
