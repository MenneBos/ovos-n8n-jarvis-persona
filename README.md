# OVOS N8N AI Agent Plugin

A custom OVOS plugin that bypasses traditional intent/persona architecture and uses n8n with agentic AI for processing queries and controlling multimedia.

## Features

- **N8N Integration**: Connects to n8n webhook endpoints for AI agent processing
- **Tool Call Processing**: Interprets JSON tool responses from n8n and executes actions
- **Multimedia Support**:
  - Spotify control via D-Bus/MPRIS (spotifyd support)
  - Audio playback (local files, URLs, sound effects)
  - Video playback (local files, URLs, streaming)
  - Image display
- **Streaming Responses**: Supports real-time streaming of AI responses
- **Extensible Architecture**: Easy to add new tool handlers

## Installation

### Using Devbox and UV (Recommended)

This project uses [Devbox](https://www.jetpack.io/devbox) for reproducible development environments and [UV](https://github.com/astral-sh/uv) for fast Python package management.

```bash
# Install Devbox (if not already installed)
curl -fsSL https://get.jetpack.io/devbox | bash

# Clone the repository
git clone https://github.com/yourusername/ovos-n8n-agent-plugin.git
cd ovos-n8n-agent-plugin

# Enter the development environment (auto-installs dependencies)
devbox shell

# The environment automatically:
# - Creates a virtual environment
# - Installs all dependencies
# - Installs the package in editable mode

# To manually install/update dependencies:
uv sync
uv pip install -e .
```

### Manual Installation

If you prefer not to use Devbox:

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install
uv venv
source .venv/bin/activate
uv sync
uv pip install -e .
```

### Development Commands

When inside the Devbox shell, you have access to these commands:

```bash
# Run tests
devbox run test

# Format code
devbox run format

# Lint code
devbox run lint

# Build package
devbox run build

# Clean build artifacts
devbox run clean

# Check Spotify/spotifyd status
devbox run spotifyd-status
devbox run dbus-check
```

## Configuration

### OVOS Configuration

Add the solver to your OVOS persona configuration (`~/.config/ovos_persona/n8n_agent.json`):

```json
{
  "name": "N8N Agent",
  "solvers": [
    "ovos-n8n-agent-plugin"
  ],
  "ovos-n8n-agent-plugin": {
    "webhook_url": "http://localhost:5678/webhook/chat",
    "api_key": "your-api-key-if-needed",
    "timeout": 30,
    "enable_streaming": true,
    "process_tools": true,
    "spotify": {
      "use_spotifyd": true,
      "device_name": "OVOS"
    },
    "audio": {
      "player_command": "auto",
      "default_volume": 50
    },
    "video": {
      "player_command": "auto",
      "fullscreen": false,
      "display": ":0"
    }
  }
}
```

### N8N Webhook Setup

1. Create a webhook trigger in n8n
2. Connect it to your AI agent workflow
3. Configure the agent to return tool calls in this format:

```json
{
  "text": "I'll play that playlist for you",
  "tool_calls": [
    {
      "tool": "spotify",
      "action": "play_playlist",
      "params": {
        "playlist_id": "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
        "shuffle": true
      }
    }
  ]
}
```

## Supported Tool Calls

### Spotify/Music

```json
{
  "tool": "spotify",
  "action": "play_playlist",
  "params": {
    "playlist_id": "spotify:playlist:xxx",
    "shuffle": true
  }
}
```

Actions: `play`, `pause`, `play_pause`, `next`, `previous`, `play_playlist`, `play_track`, `play_album`, `play_artist`, `set_volume`, `shuffle`, `repeat`

### Audio

```json
{
  "tool": "audio",
  "action": "play_file",
  "params": {
    "file": "/path/to/audio.mp3"
  }
}
```

Actions: `play_file`, `play_url`, `stop`, `pause`, `resume`, `set_volume`, `play_sound`

### Video

```json
{
  "tool": "video",
  "action": "play_url",
  "params": {
    "url": "https://example.com/video.mp4",
    "fullscreen": true
  }
}
```

Actions: `play`, `play_file`, `play_url`, `stop`, `pause`, `resume`, `fullscreen`, `show_image`

### Calculations

```json
{
  "tool": "calculate",
  "action": "evaluate",
  "params": {
    "expression": "2 + 2 * 3"
  }
}
```

## Prerequisites

### System Dependencies

- **Spotify Control**: `spotifyd` or `spotify` desktop client
- **Audio Players**: `paplay`, `mpg123`, `ffplay`, or `mpv`
- **Video Players**: `mpv`, `vlc`, `mplayer`, or `ffplay`
- **Image Viewers**: `feh` or `display` (ImageMagick)
- **D-Bus**: Required for Spotify control

### Python Dependencies

All dependencies are managed via `pyproject.toml` and automatically installed when using Devbox or UV:

- `ovos-plugin-manager>=0.0.25`
- `ovos-utils>=0.0.38`
- `requests>=2.31.0`
- `pydbus>=0.6.0`
- `aiohttp>=3.9.0`
- `websocket-client>=1.6.0`

## Usage Example

Once configured, the plugin will intercept queries and send them to your n8n webhook:

```
User: "Play my favorite playlist on Spotify"
→ Query sent to n8n webhook
→ N8N AI agent processes and returns tool call
→ Plugin executes: spotify.play_playlist({"playlist_id": "..."})
→ Music starts playing via spotifyd
```

## Development

### Project Structure

```
ovos-n8n-agent-plugin/
├── ovos_n8n_agent_plugin/
│   ├── solver.py              # Main OVOS solver implementation
│   ├── n8n_client.py          # N8N webhook communication
│   ├── command_processor.py   # Tool call routing
│   └── media_controllers/
│       ├── spotify.py         # Spotify/spotifyd control
│       ├── audio.py           # Audio playback
│       └── video.py           # Video/image display
```

### Adding New Tool Handlers

1. Add handler method to `CommandProcessor` in `command_processor.py`
2. Register in `self.tool_handlers` dictionary
3. Implement the tool logic

Example:
```python
def _handle_my_tool(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    # Implementation
    return {"success": True, "message": "Action completed"}
```

## Troubleshooting

### Spotify not responding
- Ensure `spotifyd` is running: `systemctl --user status spotifyd`
- Check D-Bus connection: `dbus-send --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames | grep spotify`

### Audio/Video playback issues
- Install required players: `sudo apt install mpv ffmpeg paplay`
- Check DISPLAY variable for video: `echo $DISPLAY`

### N8N connection errors
- Verify webhook URL is accessible
- Check firewall settings
- Test with curl: `curl -X POST http://localhost:5678/webhook/chat -H "Content-Type: application/json" -d '{"message":"test"}'`

## License

Apache License 2.0

## Contributing

Contributions are welcome! Please submit pull requests or issues on GitHub.