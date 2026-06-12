"""
Clase base para clientes LLM.
"""

import abc
import time
import os
from typing import Dict, Any

class LLMClient(abc.ABC):
    """Cliente base para proveedores LLM."""
    
    def __init__(self, agent_id: str, provider_config: Dict[str, Any], core_config: Dict[str, Any]):
        self.agent_id = agent_id
        self.provider_config = provider_config
        self.core_config = core_config
        self.api_key = self._resolve_api_key()
    
    @abc.abstractmethod
    def generate_response(self, prompt: str, system_prompt: str, config: Dict[str, Any]) -> str:
        """Genera una respuesta del LLM."""
        pass
    
    def stream_response(self, prompt: str, system_prompt: str = "", config: dict = None):
        """
        Genera respuesta con streaming.
        Por defecto, no implementado - las subclases pueden sobrescribir.
        """
        raise NotImplementedError(f"{self.__class__.__name__} no soporta streaming")
    
    def _resolve_api_key(self) -> str:
        """Resuelve la API key de variables de entorno o configuración."""
        provider_name = self.__class__.__name__.replace("Client", "").upper()
        env_var = f"{provider_name}_API_KEY"
        
        # Primero de variables de entorno
        api_key = os.environ.get(env_var)
        if api_key:
            return api_key
        
        # Luego de la configuración
        if self.provider_config.get("api_key"):
            return self.provider_config["api_key"]
        
        return ""
    
    def _log_telemetry(self, provider: str, model: str, ti: int, to: int):
        """Registra telemetría de la llamada LLM."""
        # Implementación base - puede ser sobrescrita
        pass
