# OVOS N8N Agent Plugin for JARVIS

A sophisticated OVOS Question Solver plugin that integrates with n8n workflows to create a JARVIS-like AI assistant. This plugin sends user queries to n8n webhooks where they're processed by AI agents, then executes the returned tool commands locally.

## Features

- **JARVIS Persona**: Embodies the sophisticated AI assistant from Iron Man
- **N8N Webhook Integration**: Connects to n8n workflows for AI processing
- **Daily Session Management**: Automatically creates fresh sessions each day
- **Tool Command Processing**: Executes timer, alarm, and delegates music/weather to sub-workflows
- **Streaming Support**: Real-time streaming of AI responses
- **Extensible Architecture**: Easy to add new tool handlers

## Supported Tools

### Local Tools (Handled by Plugin)
- **Timer**: Start, stop, pause, resume, status, clear timers
- **Alarm**: Set, cancel, snooze, list, enable/disable alarms

### Delegated Tools (Via N8N Sub-workflows)
- **Spotify Music**: All music playback via spotify_music sub-workflow
- **Weather**: Current conditions and forecasts via weather sub-workflow
- **Movies**: Movie information via movies MCP tool
- **Calculator**: Math calculations via calculator MCP tool

## Installation

```bash
# Clone the repository
git clone https://github.com/reklis/ovos-n8n-agent-plugin.git
cd ovos-n8n-agent-plugin

# Install in development mode
uv sync
uv pip install -e .
```

## Configuration

### OVOS Configuration

Add to your mycroft.conf (`~/.config/mycroft/mycroft.conf`):

```json
{
  "question_solvers": {
    "ovos-n8n-agent-plugin": {
      "enable_tx": true,
      "priority": 100,
      "webhook_url": "https://your-n8n.com/webhook/jarvis",
      "timeout": 30,
      "max_retries": 3,
      "enable_streaming": true,
      "process_tools": true,
      "return_text_only": false,
      "use_daily_session": true,
      "session_id_prefix": "jarvis"
    }
  }
}
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `webhook_url` | Required | Your n8n webhook endpoint URL |
| `enable_tx` | `true` | Allow solver to transmit responses |
| `priority` | `100` | Higher priority processes queries first |
| `timeout` | `30` | Request timeout in seconds |
| `max_retries` | `3` | Number of retry attempts |
| `enable_streaming` | `true` | Enable streaming responses |
| `process_tools` | `true` | Process tool commands from n8n |
| `return_text_only` | `false` | Return only text responses |
| `use_daily_session` | `true` | Create new session each day |
| `session_id_prefix` | `"jarvis"` | Prefix for session IDs |

## N8N Workflow Setup

### Import Pre-built Workflows

The `workflows/` directory contains ready-to-use n8n workflow templates:

1. **Import the workflows into n8n:**
   ```bash
   # Main JARVIS workflow (required)
   workflows/jarvis.json     # Main AI agent with JARVIS persona
   
   # Sub-workflows (import as needed)
   workflows/music.json       # Spotify MCP integration
   workflows/weather.json     # Weather service integration  
   workflows/movies.json      # Movie information via TMDB
   ```

2. **To import in n8n:**
   - Open your n8n instance
   - Go to Workflows → Import from File
   - Select each JSON file from the `workflows/` folder
   - Configure webhook URLs and API keys as needed

3. **Update webhook URL in mycroft.conf:**
   - Copy the webhook URL from the imported JARVIS workflow
   - Update `webhook_url` in your mycroft.conf configuration

### Manual Workflow Setup

If you prefer to create custom workflows, your n8n webhook should expect this format:
```json
{
  "message": "user's spoken command",
  "session_id": "jarvis-2025-01-17",
  "context": {}
}
```

### 2. Configure AI Agent Response

The AI agent should return responses matching the JARVIS persona with tool commands:

```json
{
  "response": "Very well, Sir. I've initiated a 10-minute timer for you.",
  "tool": "timer",
  "action": "start",
  "params": {
    "duration": 600000,
    "name": "timer_0"
  }
}
```

### 3. Music Sub-workflow

For music requests, delegate to a spotify_music sub-workflow:

```json
{
  "response": "Searching for Bohemian Rhapsody, Sir.",
  "tool": "spotify_music",
  "params": {
    "question": "Play Bohemian Rhapsody"
  }
}
```

### 4. Weather Sub-workflow

For weather requests:

```json
{
  "response": "Let me check the current conditions for you, Sir.",
  "tool": "weather",
  "params": {
    "location": "London",
    "forecast": true
  }
}
```

## Session Management

The plugin automatically generates daily session IDs:
- Format: `{prefix}-YYYY-MM-DD` (e.g., `jarvis-2025-01-17`)
- New session each day for fresh context
- Maintains conversation context within a day
- Configurable via `use_daily_session` and `session_id_prefix`

## Tool Command Examples

### Timer Operations
```json
// Start a timer
{
  "tool": "timer",
  "action": "start",
  "params": {
    "duration": 300000,  // 5 minutes in milliseconds
    "name": "timer_0"
  }
}

// Check timer status
{
  "tool": "timer",
  "action": "status",
  "params": {}
}
```

### Alarm Management
```json
// Set an alarm
{
  "tool": "alarm",
  "action": "set",
  "params": {
    "time": "07:00",
    "name": "morning_alarm",
    "label": "Wake up",
    "repeat_daily": true
  }
}

// Snooze alarm
{
  "tool": "alarm",
  "action": "snooze",
  "params": {
    "duration": 5  // minutes
  }
}
```

### Music Control (Delegated)
```json
{
  "tool": "spotify_music",
  "params": {
    "question": "Play some AC/DC"
  }
}
```

## System Prompts

The plugin works with two system prompts:

1. **jarvis_system_prompt.md**: Main JARVIS persona and tool routing
2. **music_system_prompt.md**: Spotify MCP sub-workflow handling

See the included prompt files for examples of how to configure your AI agent.

## Response Schema

Responses follow the schema defined in `n8n_response_schema.json`:
- Required: `success` field
- Required: `response` field with JARVIS's spoken text
- Tool-specific fields based on the operation

## Development

### Project Structure
```
ovos-n8n-agent-plugin/
├── ovos_n8n_agent_plugin/
│   ├── __init__.py
│   ├── solver.py              # Main OVOS solver
│   ├── n8n_client.py          # N8N webhook client
│   ├── command_processor.py   # Tool command router
│   └── media_controllers/
│       ├── timer.py           # Timer operations
│       └── alarm.py           # Alarm operations
├── workflows/                 # Pre-built n8n workflows
│   ├── jarvis.json           # Main JARVIS workflow
│   ├── music.json            # Spotify MCP sub-workflow
│   ├── weather.json          # Weather sub-workflow
│   └── movies.json           # Movies sub-workflow
├── config/
│   ├── mycroft.conf          # OVOS configuration
│   └── n8n_agent.json        # Plugin config example
├── jarvis_system_prompt.md   # Main JARVIS prompt
├── music_system_prompt.md    # Music sub-workflow prompt
└── n8n_response_schema.json  # Response format schema
```

### Testing

```bash
# Run tests
pytest tests/

# Test with sample webhook payload
python -m ovos_n8n_agent_plugin.test_webhook
```

### Adding New Tools

1. Add handler to `command_processor.py`:
```python
def _handle_my_tool(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    # Implementation
    return {"success": True, "message": "Completed"}
```

2. Register in `tool_handlers` dictionary
3. Update jarvis_system_prompt.md with examples
4. Update n8n_response_schema.json

## Troubleshooting

### Plugin Not Loading
- Check OVOS logs: `~/.local/state/mycroft/logs/`
- Verify plugin is installed: `pip list | grep ovos-n8n`
- Check configuration syntax in mycroft.conf

### N8N Connection Issues
- Test webhook: `curl -X POST {webhook_url} -H "Content-Type: application/json" -d '{"message":"test"}'`
- Check firewall/network settings
- Verify webhook URL is accessible

### Session Issues
- Sessions reset daily at midnight
- Check session_id format in n8n workflow logs
- Verify `use_daily_session` is enabled

## License

Apache License 2.0

## Contributing

Contributions welcome! Please submit pull requests or issues on GitHub.

## Credits

- OVOS Community for the plugin framework
- n8n for workflow automation
- Inspired by JARVIS from Marvel's Iron Man