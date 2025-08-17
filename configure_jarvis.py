#!/usr/bin/env python3
"""
Configuration helper for N8N JARVIS Persona
Helps set up the webhook URL and test connectivity
"""

import json
import os
import sys
import requests
from pathlib import Path

def test_webhook(url):
    """Test if the webhook is accessible"""
    print(f"Testing webhook: {url}")
    
    test_payload = {
        "message": "Test connection",
        "session_id": "test-session",
        "context": {}
    }
    
    try:
        response = requests.post(url, json=test_payload, timeout=5)
        if response.status_code == 404:
            return False, "404 - Webhook not found. Please check the URL and ensure n8n workflow is active."
        elif response.status_code == 200:
            return True, "Webhook is accessible!"
        else:
            return False, f"HTTP {response.status_code}: {response.text[:100]}"
    except requests.exceptions.ConnectionError:
        return False, "Connection failed. Is n8n running?"
    except requests.exceptions.Timeout:
        return False, "Request timed out"
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    print("JARVIS Persona Configuration Helper")
    print("=" * 40)
    
    # Default paths
    persona_dir = Path.home() / ".config" / "ovos_persona"
    config_file = persona_dir / "jarvis.json"
    
    # Create directory if it doesn't exist
    persona_dir.mkdir(parents=True, exist_ok=True)
    
    # Load existing config or use default
    if config_file.exists():
        print(f"Found existing config at: {config_file}")
        with open(config_file, 'r') as f:
            config = json.load(f)
        current_url = config.get("ovos-n8n-jarvis-persona", {}).get("webhook_url", "")
        print(f"Current webhook URL: {current_url}")
    else:
        print("No existing config found. Creating new configuration.")
        config = {
            "name": "JARVIS",
            "description": "Just A Rather Very Intelligent System - Tony Stark's AI assistant",
            "persona_plugin": "ovos-n8n-jarvis-persona",
            "ovos-n8n-jarvis-persona": {
                "webhook_url": "http://localhost:5678/webhook/jarvis",
                "primary_persona": True,
                "enable_streaming": True,
                "process_tools": True,
                "return_text_only": False,
                "fallback_enabled": True,
                "use_daily_session": True,
                "session_id_prefix": "jarvis",
                "timeout": 30,
                "max_retries": 3,
                "wake_words": ["jarvis", "hey jarvis", "okay jarvis"]
            }
        }
        current_url = config["ovos-n8n-jarvis-persona"]["webhook_url"]
    
    print("\n" + "=" * 40)
    print("N8N Webhook Configuration")
    print("=" * 40)
    
    # Get webhook URL
    print("\nEnter your n8n webhook URL")
    print("Examples:")
    print("  - http://localhost:5678/webhook/jarvis")
    print("  - https://your-n8n.com/webhook/jarvis")
    print(f"\nPress Enter to keep current: {current_url}")
    
    new_url = input("Webhook URL: ").strip()
    if new_url:
        config["ovos-n8n-jarvis-persona"]["webhook_url"] = new_url
    else:
        new_url = current_url
    
    # Test the webhook
    print("\n" + "=" * 40)
    print("Testing Webhook Connection")
    print("=" * 40)
    
    success, message = test_webhook(new_url)
    if success:
        print(f"✓ {message}")
    else:
        print(f"✗ {message}")
        print("\nWARNING: Webhook test failed!")
        print("Make sure:")
        print("1. N8N is running")
        print("2. The webhook workflow is active")
        print("3. The URL is correct")
        
        proceed = input("\nSave configuration anyway? (y/n): ").lower()
        if proceed != 'y':
            print("Configuration cancelled.")
            return
    
    # Save configuration
    print("\n" + "=" * 40)
    print("Saving Configuration")
    print("=" * 40)
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Configuration saved to: {config_file}")
    
    # Show next steps
    print("\n" + "=" * 40)
    print("Next Steps")
    print("=" * 40)
    print("\n1. Ensure your n8n workflow is active")
    print("2. Import the workflow examples from the 'workflows/' directory")
    print("3. Restart OVOS services:")
    print("   systemctl --user restart ovos")
    print("\n4. Test with: 'Hey JARVIS, what movies are in theaters?'")
    
    if not success:
        print("\n⚠️  Remember to fix the webhook connection before using JARVIS!")

if __name__ == "__main__":
    main()