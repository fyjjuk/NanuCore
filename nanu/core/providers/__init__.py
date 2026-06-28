from typing import Dict, Any, List
from .base import LLMClient
from .ollama import OllamaClient
from .gemini import GeminiClient
from .groq import GroqClient
from .openrouter import OpenRouterClient
from .cerebras import CerebrasClient
from .mistral import MistralClient
from .huggingface import HuggingFaceClient
from .router import LLMRouter
from .models import (
    ProviderModel,
    get_available_models,
    get_free_models,
    get_model_by_id,
    PROVIDER_MODELS
)

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
    'LLMClient', 
    'OllamaClient', 
    'GeminiClient', 
    'GroqClient',
    'OpenRouterClient',
    'CerebrasClient',
    'MistralClient',
    'HuggingFaceClient',
    'LLMRouter', 
    'create_llm_router',
    'ProviderModel',
    'get_available_models',
    'get_free_models',
    'get_model_by_id',
    'PROVIDER_MODELS'
]
