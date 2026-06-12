"""Fábrica de clientes LLM."""
from typing import Dict, Any
from nanu.core.providers.ollama import OllamaClient

def create_llm_client(config: Dict[str, Any]):
    """Crea un cliente LLM según la configuración."""
    provider = config.get('name', 'ollama').lower()
    if provider == 'ollama':
        return OllamaClient(config)
    else:
        # Por ahora solo Ollama, luego se pueden añadir más
        return OllamaClient(config)
