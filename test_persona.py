#!/usr/bin/env python3
"""
Test script for N8N JARVIS Solver
Tests the solver without running the full OVOS stack
"""

import json
import logging
import sys
from pathlib import Path
from ovos_n8n_agent_plugin.solver import N8NJarvisSolver
from ovos_n8n_agent_plugin.persona_config import get_jarvis_persona

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_solver():
    """Test the JARVIS solver with sample queries"""
    
    # Load configuration using the same method as the persona plugin
    print("Loading JARVIS persona configuration...")
    persona_config = get_jarvis_persona()
    
    # Extract solver configuration
    solver_config = persona_config.get("ovos-n8n-jarvis-solver", {})
    
    print(f"Persona Name: {persona_config.get('name')}")
    print(f"Description: {persona_config.get('description')}")
    print(f"Using webhook URL: {solver_config.get('webhook_url')}")
    print(f"Session prefix: {solver_config.get('session_id_prefix')}")
    print("-" * 50)
    
    # Initialize solver
    print("\nInitializing JARVIS Solver...")
    try:
        solver = N8NJarvisSolver(config=solver_config)
        print("✓ Solver initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize solver: {e}")
        sys.exit(1)
    
    # Test queries
    test_queries = [
        "What movies are in theaters right now?",
        "What's the weather like today?",
        "Set a timer for 5 minutes",
        "Play some music",
        "What time is it?",
        "Tell me a joke"
    ]
    
    print("\n" + "="*50)
    print("Testing JARVIS Solver")
    print("="*50 + "\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"[{i}/{len(test_queries)}] Query: {query}")
        
        # Get response using ChatMessageSolver interface
        try:
            # Format as chat messages
            messages = [
                {"role": "user", "content": query}
            ]
            
            print("  Sending to N8N webhook...")
            response = solver.get_chat_completion(messages, lang="en-US")
            
            if response:
                try:
                    # Safely format response for display
                    if isinstance(response, str):
                        display_text = response[:200] + ('...' if len(response) > 200 else '')
                    else:
                        display_text = str(response)[:200] + ('...' if len(str(response)) > 200 else '')
                    print(f"  ✓ Response: {display_text}")
                except Exception as e:
                    print(f"  ✓ Response received but error displaying: {e}")
                    print(f"     Response type: {type(response)}")
            else:
                print("  ✗ No response received")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        print("-"*50 + "\n")
    
    # Test streaming if enabled
    if solver_config.get("enable_streaming", False):
        print("Testing streaming response...")
        try:
            messages = [{"role": "user", "content": "Tell me about JARVIS from Iron Man"}]
            print("  Streaming: ", end="", flush=True)
            for chunk in solver.stream_utterances(messages, lang="en-US"):
                print(chunk, end="", flush=True)
            print("\n")
        except Exception as e:
            print(f"\n  ✗ Streaming error: {e}")
    
    # Cleanup
    print("\nShutting down solver...")
    try:
        solver.shutdown()
        print("✓ Solver shutdown complete")
    except Exception as e:
        print(f"✗ Shutdown error: {e}")
    
    print("\n" + "="*50)
    print("Test complete!")
    print("="*50)

if __name__ == "__main__":
    test_solver()