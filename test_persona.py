#!/usr/bin/env python3
"""
Test script for N8N JARVIS Persona
Tests the persona without running the full OVOS stack
"""

import json
import logging
from ovos_n8n_agent_plugin.persona import N8NJarvisPersona

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def test_persona():
    """Test the JARVIS persona with sample queries"""
    
    # Create test configuration
    config = {
        "name": "JARVIS",
        "description": "Just A Rather Very Intelligent System",
        "webhook_url": "http://localhost:5678/webhook/jarvis",  # Update with your n8n URL
        "primary_persona": True,
        "enable_streaming": False,  # Disable streaming for simple test
        "process_tools": True,
        "return_text_only": False,
        "fallback_enabled": True,
        "use_daily_session": True,
        "session_id_prefix": "jarvis-test",
        "timeout": 30
    }
    
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
        
        # Test match confidence
        confidence = persona.match(query)
        print(f"Match confidence: {confidence}")
        
        # Get response
        try:
            response = persona.get_response(query)
            if response:
                print(f"Response: {response}")
            else:
                print("No response received")
        except Exception as e:
            print(f"Error: {e}")
        
        print("-"*40 + "\n")
    
    # Cleanup
    persona.shutdown()
    print("Test complete!")

if __name__ == "__main__":
    test_persona()