"""Base de datos de modelos disponibles por proveedor."""

from typing import Dict, List, Optional

class ProviderModel:
    """Representa un modelo disponible en un proveedor."""
    def __init__(self, provider: str, model_id: str, display_name: str = None, 
                 context_length: int = None, input_cost: float = None, 
                 output_cost: float = None, is_free: bool = True):
        self.provider = provider
        self.model_id = model_id
        self.display_name = display_name or model_id
        self.context_length = context_length or 8192
        self.input_cost = input_cost or 0.0
        self.output_cost = output_cost or 0.0
        self.is_free = is_free

# Modelos disponibles por proveedor
PROVIDER_MODELS: Dict[str, List[ProviderModel]] = {
    "ollama": [
        ProviderModel("ollama", "phi3:mini", "Phi3 Mini", 8192, 0, 0, True),
        ProviderModel("ollama", "qwen2.5:0.5b", "Qwen2.5 0.5B", 8192, 0, 0, True),
        ProviderModel("ollama", "llama3.2:3b", "Llama3.2 3B", 8192, 0, 0, True),
        ProviderModel("ollama", "deepseek-r1:7b", "DeepSeek R1 7B", 16384, 0, 0, True),
        ProviderModel("ollama", "gemma4:e4b", "Gemma 4 E4B", 8192, 0, 0, True),
        ProviderModel("ollama", "qwen2.5-coder:7b", "Qwen2.5 Coder 7B", 8192, 0, 0, True),
    ],
    "gemini": [
        ProviderModel("gemini", "gemini-2.0-flash-exp", "Gemini 2.0 Flash Exp", 8192, 0, 0, True),
        ProviderModel("gemini", "gemini-1.5-flash", "Gemini 1.5 Flash", 8192, 0, 0, True),
        ProviderModel("gemini", "gemini-1.5-pro", "Gemini 1.5 Pro", 8192, 0, 0, False),
    ],
    "groq": [
        ProviderModel("groq", "llama-3.3-70b-versatile", "Llama3.3 70B Versatile", 8192, 0, 0, True),
        ProviderModel("groq", "llama3-8b-8192", "Llama3 8B", 8192, 0, 0, True),
        ProviderModel("groq", "mixtral-8x7b-32768", "Mixtral 8x7B", 32768, 0, 0, True),
        ProviderModel("groq", "gemma2-9b-it", "Gemma2 9B", 8192, 0, 0, True),
    ],
    "cerebras": [
        ProviderModel("cerebras", "llama3.3-70b", "Llama3.3 70B", 8192, 0, 0, True),
    ],
    "openrouter": [
        ProviderModel("openrouter", "meta-llama/llama-3.3-70b-instruct", "Llama3.3 70B", 8192, 0, 0, True),
        ProviderModel("openrouter", "google/gemini-2.0-flash-exp", "Gemini 2.0 Flash Exp", 8192, 0, 0, True),
        ProviderModel("openrouter", "microsoft/phi-3.5-mini-128k-instruct", "Phi3.5 Mini", 8192, 0, 0, True),
        ProviderModel("openrouter", "deepseek/deepseek-chat", "DeepSeek Chat", 8192, 0, 0, True),
    ],
    "mistral": [
        ProviderModel("mistral", "mistral-small-latest", "Mistral Small", 8192, 0, 0, True),
        ProviderModel("mistral", "mistral-medium-latest", "Mistral Medium", 8192, 0, 0, False),
    ],
    "huggingface": [
        ProviderModel("huggingface", "meta-llama/Llama-3.2-3B-Instruct", "Llama3.2 3B", 8192, 0, 0, True),
        ProviderModel("huggingface", "microsoft/Phi-3.5-mini-instruct", "Phi3.5 Mini", 8192, 0, 0, True),
    ],
}

def get_available_models(provider: Optional[str] = None) -> List[ProviderModel]:
    """Obtiene la lista de modelos disponibles para un proveedor."""
    if provider:
        return PROVIDER_MODELS.get(provider, [])
    all_models = []
    for models in PROVIDER_MODELS.values():
        all_models.extend(models)
    return all_models

def get_free_models(provider: Optional[str] = None) -> List[ProviderModel]:
    """Obtiene modelos gratuitos."""
    models = get_available_models(provider)
    return [m for m in models if m.is_free]

def get_model_by_id(provider: str, model_id: str) -> Optional[ProviderModel]:
    """Obtiene un modelo específico por proveedor y ID."""
    models = PROVIDER_MODELS.get(provider, [])
    for m in models:
        if m.model_id == model_id:
            return m
    return None

__all__ = [
    'ProviderModel',
    'PROVIDER_MODELS',
    'get_available_models',
    'get_free_models',
    'get_model_by_id'
]
