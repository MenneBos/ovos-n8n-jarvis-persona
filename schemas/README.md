# N8N Webhook Schemas

This directory contains JSON schemas for the n8n webhook integration with the JARVIS persona.

## Files

- **n8n_request_schema.json**: Schema for requests sent FROM the JARVIS persona TO the n8n webhook
- **n8n_response_schema.json**: Schema for responses sent FROM n8n TO the JARVIS persona
- **response_examples.json**: Example responses for different scenarios

## Usage in N8N

### Setting up the Webhook Node

1. In your n8n workflow, add a **Webhook** node as the trigger
2. Set the HTTP Method to **POST**
3. Set the path to match your configuration (e.g., `/webhook/jarvis`)
4. Enable **Response Data** to return custom responses

### Processing the Request

The webhook will receive a JSON payload matching the request schema:

```json
{
  "message": "What movies are in theaters?",
  "session_id": "jarvis-2024-01-15",
  "context": {
    "skill_id": "persona.openvoiceos",
    "source": "audio"
  }
}
```

### Returning Responses

Your n8n workflow should return responses matching one of these formats:

#### Simple Text Response
```json
{
  "response": "Sir, the latest Marvel movie 'Deadpool & Wolverine' is currently showing in theaters, along with 'Inside Out 2' and 'Twisters'."
}
```

#### Response with Tool Calls
```json
{
  "response": "Setting a 5-minute timer for you, Sir.",
  "tool_calls": [
    {
      "tool": "timer",
      "action": "start",
      "params": {
        "duration": 300,
        "label": "General timer"
      }
    }
  ]
}
```

#### Error Response
```json
{
  "error": "service_unavailable",
  "message": "I'm unable to access that information at the moment, Sir."
}
```

## N8N Workflow Tips

### Using AI Agents
When using AI Agent nodes in n8n:
1. Pass the `message` field to your AI agent's prompt
2. Use the `session_id` for conversation memory
3. Return structured JSON responses

### Using Sub-workflows
For complex operations, use sub-workflows:
- **spotify_music**: Handle music playback requests
- **weather**: Get weather information
- **movies**: Query movie databases
- **calculator**: Perform calculations

### Response Node Configuration
In your final **Respond to Webhook** node:
1. Set **Response Code** to 200
2. Set **Response Headers** to include `Content-Type: application/json`
3. Use an expression to format your response:

```javascript
{
  "response": $json["agent_response"],
  "tool_calls": $json["tool_calls"] || undefined
}
```

## Testing

Use the test files in the `tests/` directory to verify your webhook:

```bash
# Test movie query
curl -X POST http://localhost:5678/webhook/jarvis \
  -H "Content-Type: application/json" \
  -d @tests/movie.json

# Test timer command
curl -X POST http://localhost:5678/webhook/jarvis \
  -H "Content-Type: application/json" \
  -d @tests/timer.json
```