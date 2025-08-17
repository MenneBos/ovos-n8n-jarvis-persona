from .solver import N8NJarvisSolver
from .persona_config import get_jarvis_persona

# For backward compatibility
N8NJarvisPersona = N8NJarvisSolver

__version__ = "0.2.0"
__all__ = ["N8NJarvisSolver", "get_jarvis_persona", "N8NJarvisPersona"]