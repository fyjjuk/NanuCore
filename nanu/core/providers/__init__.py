from typing import Dict, Any, List
from .base import LLMClient
from .ollama import OllamaClient
from .gemini import GeminiClient
from .groq import GroqClient
from .router import LLMRouter

def create_llm_router(config: Dict[str, Any]) -> LLMRouter:
    """Crea un router LLM a partir de la configuración."""
    providers_config = config.get('providers', [])
    if not providers_config:
        providers_config = [{"type": "ollama", "name": "ollama", "model": "phi3:mini"}]
    
    # Añadir nombres por defecto si no tienen
    for p in providers_config:
        if 'name' not in p:
            p['name'] = p.get('type', 'unknown')
    
    return LLMRouter(providers_config)

__all__ = [
    'LLMClient', 'OllamaClient', 'GeminiClient', 'GroqClient',
    'LLMRouter', 'create_llm_router'
]
