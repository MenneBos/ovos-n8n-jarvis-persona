#!/usr/bin/env python3
"""
Test script for JARVIS Persona implementation
"""

import sys
import json
from pathlib import Path

def test_persona_import():
    """Test if the persona can be imported"""
    print("Testing JARVIS Persona Installation")
    print("=" * 60)
    
    print("\n1. Testing module import...")
    try:
        from ovos_n8n_agent_plugin.persona import N8NJarvisPersona
        print("   ✓ N8NJarvisPersona imported successfully")
        print("   Package: ovos-n8n-jarvis-persona")
        return True
    except ImportError as e:
        print(f"   ✗ Failed to import: {e}")
        print("   Try: pip install -e .")
        return False

def test_persona_instantiation():
    """Test if persona can be instantiated"""
    print("\n2. Testing persona instantiation...")
    
    try:
        from ovos_n8n_agent_plugin.persona import N8NJarvisPersona
        
        # Test config
        config = {
            "name": "JARVIS",
            "webhook_url": "http://localhost:5678/webhook/test",
            "primary_persona": True,
            "enable_streaming": False,
            "process_tools": True
        }
        
        # Create persona
        persona = N8NJarvisPersona(config)
        print(f"   ✓ Persona created: {persona.name}")
        print(f"     Description: {persona.description}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Failed to instantiate: {e}")
        return False

def test_persona_match():
    """Test persona matching logic"""
    print("\n3. Testing persona matching...")
    
    try:
        from ovos_n8n_agent_plugin.persona import N8NJarvisPersona
        
        # Test as primary persona
        config = {
            "webhook_url": "http://localhost:5678/webhook/test",
            "primary_persona": True
        }
        
        persona = N8NJarvisPersona(config)
        
        # Test matching
        test_utterances = [
            "What time is it?",
            "Hey JARVIS, play some music",
            "Set a timer for 5 minutes"
        ]
        
        print("   Primary persona mode:")
        for utterance in test_utterances:
            confidence = persona.match(utterance)
            print(f"     '{utterance}' → confidence: {confidence}")
        
        # Test with wake words
        config["primary_persona"] = False
        config["wake_words"] = ["jarvis", "hey jarvis"]
        persona = N8NJarvisPersona(config)
        
        print("\n   Wake word mode:")
        for utterance in test_utterances:
            confidence = persona.match(utterance)
            print(f"     '{utterance}' → confidence: {confidence}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error in matching: {e}")
        return False

def test_persona_response():
    """Test persona response generation"""
    print("\n4. Testing response generation...")
    
    try:
        from ovos_n8n_agent_plugin.persona import N8NJarvisPersona
        
        # Load config if available
        config_path = Path.home() / ".config" / "ovos_persona" / "jarvis.json"
        
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
                config = config.get("ovos-n8n-jarvis-persona", {})
            print(f"   Using config from: {config_path}")
        else:
            config = {
                "webhook_url": "http://localhost:5678/webhook/jarvis",
                "primary_persona": True,
                "enable_streaming": False
            }
            print("   Using test config")
        
        persona = N8NJarvisPersona(config)
        
        # Test query
        test_query = "What is the weather today?"
        print(f"\n   Testing query: '{test_query}'")
        
        try:
            response = persona.get_response(test_query)
            if response:
                print(f"   ✓ Response: {response}")
            else:
                print("   ⚠ No response (webhook may be offline)")
        except Exception as e:
            print(f"   ⚠ Response error: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def test_entry_points():
    """Check if persona entry point is registered"""
    print("\n5. Testing entry point registration...")
    
    try:
        import pkg_resources
        
        # Check persona entry points
        print("   Checking persona plugins:")
        persona_found = False
        for ep in pkg_resources.iter_entry_points('ovos.plugin.persona'):
            print(f"     - {ep.name}")
            if 'jarvis' in ep.name.lower():
                persona_found = True
                print(f"       ✓ JARVIS persona found!")
        
        if not persona_found:
            print("   ⚠ JARVIS persona not in entry points")
        
        # Also check solver entry points
        print("\n   Checking solver plugins (for compatibility):")
        solver_found = False
        for ep in pkg_resources.iter_entry_points('ovos.plugin.solver'):
            if 'n8n' in ep.name.lower():
                print(f"     - {ep.name} (solver mode still available)")
                solver_found = True
        
        return persona_found
        
    except Exception as e:
        print(f"   ✗ Error checking entry points: {e}")
        return False

def test_plugin_manager():
    """Test if OVOS plugin manager can find the persona"""
    print("\n6. Testing OVOS plugin manager...")
    
    try:
        from ovos_plugin_manager.templates.persona import find_persona_plugins
        
        plugins = find_persona_plugins()
        print(f"   Found {len(plugins)} persona plugins:")
        
        found = False
        for name, plugin in plugins.items():
            print(f"     - {name}")
            if 'jarvis' in name.lower() or 'n8n' in name.lower():
                found = True
                print(f"       ✓ JARVIS persona found in plugin manager!")
        
        if not found:
            print("   ⚠ JARVIS persona not found in plugin manager")
            print("   Try: pip install -e . --force-reinstall")
        
        return found
        
    except ImportError:
        print("   ⚠ ovos-plugin-manager not installed")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def check_persona_config():
    """Check if persona config exists"""
    print("\n7. Checking persona configuration...")
    
    config_locations = [
        Path.home() / ".config" / "ovos_persona" / "jarvis.json",
        Path.home() / ".config" / "mycroft" / "mycroft.conf"
    ]
    
    found_config = False
    
    for config_path in config_locations:
        if config_path.exists():
            print(f"   ✓ Found config: {config_path}")
            
            if config_path.name == "jarvis.json":
                try:
                    with open(config_path) as f:
                        config = json.load(f)
                    print(f"     Persona: {config.get('name')}")
                    print(f"     Plugin: {config.get('persona_plugin')}")
                    webhook = config.get("ovos-n8n-jarvis-persona", {}).get("webhook_url")
                    print(f"     Webhook: {webhook}")
                    found_config = True
                except Exception as e:
                    print(f"     ✗ Error reading config: {e}")
    
    if not found_config:
        print("   ⚠ No persona config found")
        print("   Create ~/.config/ovos_persona/jarvis.json")
        print("   Or add persona config to mycroft.conf")
    
    return found_config

def main():
    print("="*60)
    print("JARVIS PERSONA INSTALLATION TEST")
    print("="*60)
    
    results = {
        "Import": test_persona_import(),
        "Instantiation": test_persona_instantiation(),
        "Matching": test_persona_match(),
        "Response": test_persona_response(),
        "Entry Points": test_entry_points(),
        "Plugin Manager": test_plugin_manager(),
        "Configuration": check_persona_config()
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:.<30} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    
    if all_passed:
        print("✓ All tests passed! JARVIS persona is ready.")
        print("\nNext steps:")
        print("1. Configure webhook URL in jarvis.json")
        print("2. Import n8n workflows")
        print("3. Restart OVOS")
        print("4. Say 'Hey JARVIS'")
    else:
        print("\nTROUBLESHOOTING:")
        
        if not results["Import"]:
            print("\n1. Module not found:")
            print("   pip install -e .")
        
        if not results["Entry Points"]:
            print("\n2. Entry point not registered:")
            print("   pip install -e . --force-reinstall")
        
        if not results["Configuration"]:
            print("\n3. Missing config:")
            print("   cp config/jarvis_persona.json ~/.config/ovos_persona/jarvis.json")
            print("   Edit webhook URL in jarvis.json")
        
        if not results["Plugin Manager"]:
            print("\n4. Plugin manager issue:")
            print("   pip install ovos-plugin-manager --upgrade")
    
    print("\nFor more details, see README_PERSONA.md")
    print("="*60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())