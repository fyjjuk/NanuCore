"""Router de LLM con fallback y rotación."""
import asyncio
from typing import List, Dict, Any, Optional
from .base import LLMClient
from .ollama import OllamaClient
from .gemini import GeminiClient
from .groq import GroqClient

class LLMRouter:
    """Enruta solicitudes a múltiples proveedores LLM con fallback."""
    
    def __init__(self, providers_config: List[Dict[str, Any]]):
        self.providers: List[LLMClient] = []
        self._current_index = 0
        self._lock = asyncio.Lock()
        
        for cfg in providers_config:
            provider_type = cfg.get('type', 'ollama').lower()
            if provider_type == 'ollama':
                self.providers.append(OllamaClient(cfg))
            elif provider_type == 'gemini':
                self.providers.append(GeminiClient(cfg))
            elif provider_type == 'groq':
                self.providers.append(GroqClient(cfg))
    
    async def _get_available_provider(self) -> Optional[LLMClient]:
        """Obtiene el primer proveedor disponible en orden rotatorio."""
        async with self._lock:
            if not self.providers:
                return None
            # Probar desde el índice actual
            for i in range(len(self.providers)):
                idx = (self._current_index + i) % len(self.providers)
                provider = self.providers[idx]
                if await provider.available():
                    self._current_index = (idx + 1) % len(self.providers)
                    print(f"[LLM Router] Usando: {provider.name} ({provider.model})")
                    return provider
            return None
    
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Genera respuesta usando el primer proveedor disponible."""
        provider = await self._get_available_provider()
        if not provider:
            return "Error: No hay proveedores LLM disponibles"
        
        try:
            return await provider.generate(prompt, system_prompt, **kwargs)
        except Exception as e:
            print(f"[LLM Router] Error con {provider.name}: {e}")
            # Reintentar con el siguiente proveedor
            return await self.generate(prompt, system_prompt, **kwargs)
    
    async def generate_with_retry(self, prompt: str, system_prompt: str = "", 
                                   max_retries: int = 3, **kwargs) -> str:
        """Genera respuesta con reintentos en caso de fallo."""
        last_error = None
        for attempt in range(max_retries):
            try:
                return await self.generate(prompt, system_prompt, **kwargs)
            except Exception as e:
                last_error = e
                print(f"[LLM Router] Intento {attempt + 1} falló: {e}")
                await asyncio.sleep(1)
        return f"Error después de {max_retries} intentos: {last_error}"
