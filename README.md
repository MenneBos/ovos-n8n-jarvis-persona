# OVOS N8N JARVIS Persona Plugin

A sophisticated OVOS Persona plugin that embodies JARVIS from Iron Man, processing all queries through n8n workflows with AI agents to create an intelligent, character-driven assistant experience.

## Features

- **JARVIS Persona**: Full character embodiment of Tony Stark's AI assistant
- **N8N Webhook Integration**: All queries processed through n8n workflows
- **Daily Session Management**: Automatic session rotation for context management
- **Simple Response Processing**: Clean text responses from n8n workflows
- **Streaming Support**: Natural speech with streamed responses
- **Primary Interface**: Can replace standard OVOS intent system

## N8N Integration

All functionality is handled by the n8n server through simple request/response:
- **Music Control**: Handled by n8n workflows
- **Weather**: Processed through n8n AI agents
- **Movies**: Information via n8n integrations
- **Calculations**: Math and conversions via n8n
- **General Queries**: All processed by n8n AI with JARVIS personality

## Installation

```bash
# Clone the repository
git clone https://github.com/reklis/ovos-n8n-jarvis-persona.git
cd ovos-n8n-jarvis-persona

# Install in development mode
pip install -e .

# Or install from pip (when published)
pip install ovos-n8n-jarvis-persona

# Quick setup (runs all steps)
./setup.sh
```

## Configuration

### 1. Create Persona Config

Copy the JARVIS persona config to OVOS persona directory:

```bash
mkdir -p ~/.config/ovos_persona/
cp config/jarvis_persona.json ~/.config/ovos_persona/jarvis.json
```

Edit `~/.config/ovos_persona/jarvis.json` with your n8n webhook URL:

```json
{
  "name": "JARVIS",
  "description": "Just A Rather Very Intelligent System",
  "persona_plugin": "ovos-n8n-jarvis-persona",
  "ovos-n8n-jarvis-persona": {
    "webhook_url": "https://your-n8n.com/webhook/jarvis",
    "primary_persona": true,
    "enable_streaming": true,
    "process_tools": true,
    "use_daily_session": true,
    "session_id_prefix": "jarvis",
    "timeout": 30
  }
}
```

### 2. Update OVOS Configuration

Add to your mycroft.conf (`~/.config/mycroft/mycroft.conf`):

```json
{
  "lang": "en-us",
  "listener": {
    "wake_word": "hey_jarvis"
  },
  "hotwords": {
    "hey_jarvis": {
      "module": "ovos-ww-plugin-openwakeword",
      "threshold": 0.3
    }
  },
  "intents": {
    "persona": {
      "enabled": true,
      "default_persona": "jarvis",
      "personas_path": "~/.config/ovos_persona/"
    },
    "pipeline": [
      "stop_high",
      "converse",
      "ovos-persona",
      "padatious_high",
      "adapt_high",
      "common_qa",
      "fallback_high",
      "fallback_low"
    ]
  }
}
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `webhook_url` | Required | Your n8n webhook endpoint URL |
| `primary_persona` | `true` | If true, handles all queries |
| `enable_streaming` | `true` | Enable streaming responses |
| `process_tools` | `false` | Reserved for future use |
| `return_text_only` | `false` | Return only text without tool execution |
| `fallback_enabled` | `true` | Act as fallback when not primary |
| `use_daily_session` | `true` | Create new session each day |
| `session_id_prefix` | `"jarvis"` | Prefix for session IDs |
| `wake_words` | `["jarvis"]` | Wake words to trigger persona |
| `timeout` | `30` | Request timeout in seconds |

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

3. **Update webhook URL in jarvis.json:**
   - Copy the webhook URL from the imported JARVIS workflow
   - Update `webhook_url` in your jarvis.json configuration

### Expected Webhook Format

Your n8n webhook receives:
```json
{
  "message": "user's spoken command",
  "session_id": "jarvis-2025-01-17",
  "current_time": "2025-01-17T14:30:00.000Z",
  "location": {
    "city": "New York",
    "state": "NY",
    "country": "USA",
    "timezone": "America/New_York"
  },
  "context": {}
}
```

And should return:
```json
{
  "response": "My pleasure, Sir"
}
```

## Session Management

The plugin automatically generates daily session IDs:
- Format: `{prefix}-YYYY-MM-DD` (e.g., `jarvis-2025-01-17`)
- New session each day for fresh context
- Maintains conversation context within a day
- Configurable via `use_daily_session` and `session_id_prefix`

## How It Works

1. **User speaks** → "Hey JARVIS, set a timer for 5 minutes"
2. **OVOS processes** → Wake word detected, routes to JARVIS persona
3. **Persona sends to n8n** → Query sent to webhook with session ID
4. **N8N workflow runs** → AI agent processes with JARVIS personality
5. **Response returned** → JARVIS responds with appropriate text

## Testing Installation

```bash
# Run the persona test
python test_persona.py
```

The test will verify:
- Module import
- Persona instantiation
- Matching logic
- Entry point registration
- Configuration files
- Plugin manager detection

## Response Examples

### Simple Responses
```json
{
  "response": "Right away, Sir. I'll handle that for you."
}
```

```json
{
  "response": "Of course, Sir. Consider it done."
}
```

```json
{
  "response": "My pleasure, Sir."
}
```

## System Prompts

The plugin works with two system prompts:

1. **jarvis_system_prompt.md**: Main JARVIS persona prompt
2. **music_system_prompt.md**: Music handling prompts

## Project Structure

```
ovos-n8n-agent-plugin/
├── ovos_n8n_agent_plugin/
│   ├── __init__.py
│   ├── persona.py             # JARVIS persona implementation
│   └── n8n_client.py          # N8N webhook client
├── workflows/                 # Pre-built n8n workflows
│   ├── jarvis.json           # Main JARVIS workflow
│   ├── music.json            # Spotify MCP sub-workflow
│   ├── weather.json          # Weather sub-workflow
│   └── movies.json           # Movies sub-workflow
├── config/
│   ├── jarvis_persona.json  # Persona configuration
│   └── mycroft_persona.conf # Example OVOS config
├── jarvis_system_prompt.md  # Main JARVIS prompt
├── music_system_prompt.md   # Music sub-workflow prompt
└── n8n_response_schema.json # Response format schema
```

## Troubleshooting

### Persona Not Loading

1. **Check installation:**
   ```bash
   python -c "import ovos_n8n_agent_plugin; print(ovos_n8n_agent_plugin.__version__)"
   ```

2. **Verify entry point:**
   ```bash
   python -c "from ovos_plugin_manager.templates.persona import find_persona_plugins; print(find_persona_plugins())"
   ```

3. **Reinstall if needed:**
   ```bash
   pip install -e . --force-reinstall
   ```

### Persona Not Responding

1. **Check configuration:**
   ```bash
   cat ~/.config/ovos_persona/jarvis.json
   ```

2. **Verify OVOS pipeline:**
   - Ensure `ovos-persona` is in intent pipeline
   - Check `persona.enabled` is true

3. **Test webhook:**
   ```bash
   curl -X POST https://your-n8n.com/webhook/jarvis \
     -H "Content-Type: application/json" \
     -d '{"message":"test","session_id":"jarvis-2025-01-17"}'
   ```

4. **Check logs:**
   ```bash
   tail -f ~/.local/state/mycroft/logs/skills.log
   ```

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -e .` in plugin directory |
| Entry point not found | Reinstall with `pip install -e . --force-reinstall` |
| Webhook timeout | Check n8n is running and URL is correct |
| No response | Verify webhook returns proper JSON format |
| Config not loaded | Ensure jarvis.json is valid JSON |

## Message Bus Events

The persona integrates with OVOS message bus for system events.

Listen to events:
```bash
ovos-cli-client monitor
```

## License

Apache License 2.0

## Contributing

Contributions welcome! Please submit pull requests or issues on GitHub.

## Credits

- OVOS Community for the plugin framework
- n8n for workflow automation
- Inspired by JARVIS from Marvel's Iron Man