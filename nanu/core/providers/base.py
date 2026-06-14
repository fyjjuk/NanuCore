"""Cliente base para proveedores LLM."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class LLMClient(ABC):
    """Cliente base para todos los proveedores LLM."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get('name', 'unknown')
        self.model = config.get('model', 'unknown')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 2048)
        self.timeout = config.get('timeout', 30)
    
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Genera una respuesta del LLM."""
        pass
    
    @abstractmethod
    async def available(self) -> bool:
        """Verifica si el proveedor está disponible (API key válida, servicio accesible)."""
        pass
