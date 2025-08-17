"""JARVIS Persona configuration for OVOS"""
import json
import os
from pathlib import Path
from ovos_utils.log import LOG

logger = LOG.create_logger(__name__)


def get_jarvis_persona():
    """
    Returns the JARVIS persona configuration.
    First tries to load from ~/.config/ovos_persona/jarvis.json,
    falls back to defaults if not found.
    """
    # Try to load user configuration
    config_path = Path.home() / ".config" / "ovos_persona" / "jarvis.json"
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                logger.info(f"Loaded JARVIS config from {config_path}")
                
                # Extract the n8n configuration section
                n8n_config = user_config.get("ovos-n8n-jarvis-solver", {})
                
                # Build the persona configuration
                return {
                    "name": user_config.get("name", "JARVIS"),
                    "description": user_config.get("description", 
                                  "Just A Rather Very Intelligent System - Tony Stark's AI assistant"),
                    "solvers": [
                        "ovos-n8n-jarvis-solver"  # Our N8N solver plugin
                    ],
                    "ovos-n8n-jarvis-solver": n8n_config
                }
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
    
    # Default configuration if file doesn't exist or fails to load
    logger.info("Using default JARVIS configuration")
    return {
        "name": "JARVIS",
        "description": "Just A Rather Very Intelligent System - Tony Stark's AI assistant",
        "solvers": [
            "ovos-n8n-jarvis-solver"  # Our N8N solver plugin
        ],
        "ovos-n8n-jarvis-solver": {
            "enabled": True,
            "webhook_url": "https://n8n.0x5f.sh/webhook/3eb829d2-c64c-479e-a0e2-ed6f7d1aa052",
            "primary_persona": True,
            "enable_streaming": True,
            "process_tools": True,
            "return_text_only": False,
            "fallback_enabled": True,
            "use_daily_session": True,
            "session_id_prefix": "jarvis",
            "timeout": 30,
            "max_retries": 3
        }
    }