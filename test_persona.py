#!/usr/bin/env python3
"""
Test script for N8N JARVIS Persona
Tests the persona without running the full OVOS stack
"""

import json
import logging
import os
from pathlib import Path
from ovos_n8n_agent_plugin.persona import N8NJarvisPersona

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def test_persona():
    """Test the JARVIS persona with sample queries"""
    
    # Load configuration from ~/.config/ovos_persona/jarvis.json
    config_path = Path.home() / ".config" / "ovos_persona" / "jarvis.json"
    
    if config_path.exists():
        print(f"Loading config from {config_path}")
        with open(config_path, 'r') as f:
            full_config = json.load(f)
            # Extract the n8n config section
            config = full_config.get("ovos-n8n-jarvis-persona", {})
            config["name"] = full_config.get("name", "JARVIS")
            config["description"] = full_config.get("description", "Just A Rather Very Intelligent System")
    else:
        print(f"Config file not found at {config_path}, using defaults")
        # Fallback configuration
        config = {
            "name": "JARVIS",
            "description": "Just A Rather Very Intelligent System",
            "webhook_url": "https://n8n.0x5f.sh/webhook/3eb829d2-c64c-479e-a0e2-ed6f7d1aa052",
            "primary_persona": True,
            "enable_streaming": False,  # Disable streaming for simple test
            "process_tools": True,
            "return_text_only": False,
            "fallback_enabled": True,
            "use_daily_session": True,
            "session_id_prefix": "jarvis-test",
            "timeout": 30
        }
    
    print(f"Using webhook URL: {config.get('webhook_url')}")
    
    # Initialize persona
    print("Initializing JARVIS Persona...")
    persona = N8NJarvisPersona(config=config)
    
    # Test queries
    test_queries = [
        "What movies are in theaters right now?",
        "What's the weather like today?",
        "Set a timer for 5 minutes",
        "Play some music"
    ]
    
    print("\n" + "="*50)
    print("Testing JARVIS Persona")
    print("="*50 + "\n")
    
    for query in test_queries:
        print(f"Query: {query}")
        
        # Get response using ChatMessageSolver interface
        try:
            # Format as chat messages
            messages = [
                {"role": "user", "content": query}
            ]
            response = persona.get_chat_completion(messages, lang="en-US")
            if response:
                print(f"Response: {response}")
            else:
                print("No response received")
        except Exception as e:
            print(f"Error: {e}")
        
        print("-"*40 + "\n")
    
    print("Test complete!")

if __name__ == "__main__":
    test_persona()