"""Fábrica de clientes LLM con múltiples proveedores."""
from typing import List, Dict, Any
from .router import LLMRouter

def create_llm_router(config: Dict[str, Any]) -> LLMRouter:
    """
    Crea un router LLM a partir de la configuración.
    
    Configuración esperada:
    {
        "providers": [
            {"type": "ollama", "model": "phi3:mini", "host": "http://localhost:11434"},
            {"type": "gemini", "model": "gemini-1.5-flash", "api_key": "..."},
            {"type": "groq", "model": "llama3-8b-8192", "api_key": "..."}
        ]
    }
    """
    providers_config = config.get('providers', [])
    if not providers_config:
        # Fallback a Ollama por defecto
        providers_config = [{"type": "ollama", "model": "phi3:mini"}]
    
    return LLMRouter(providers_config)
