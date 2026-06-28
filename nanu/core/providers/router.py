"""Router de LLM con fallback, rotación y selección de modelos."""
import asyncio
from typing import List, Dict, Any, Optional
from .base import LLMClient
from .ollama import OllamaClient
from .gemini import GeminiClient
from .groq import GroqClient
from .openrouter import OpenRouterClient
from .cerebras import CerebrasClient
from .mistral import MistralClient
from .huggingface import HuggingFaceClient
from .models import get_model_by_id, get_free_models, ProviderModel

class LLMRouter:
    """Enruta solicitudes a múltiples proveedores LLM con fallback."""
    
    # Mapa de tipos de proveedores a clases
    PROVIDER_CLASSES = {
        'ollama': OllamaClient,
        'gemini': GeminiClient,
        'groq': GroqClient,
        'openrouter': OpenRouterClient,
        'cerebras': CerebrasClient,
        'mistral': MistralClient,
        'huggingface': HuggingFaceClient,
    }
    
    def __init__(self, providers_config: List[Dict[str, Any]]):
        self.providers: List[LLMClient] = []
        self._current_index = 0
        self._lock = asyncio.Lock()
        self._provider_model_map: Dict[str, List[ProviderModel]] = {}
        self._rate_limit_status: Dict[str, float] = {}  # provider_name -> timestamp de expiración
        
        for cfg in providers_config:
            provider_type = cfg.get('type', 'ollama').lower()
            client_class = self.PROVIDER_CLASSES.get(provider_type)
            
            if not client_class:
                print(f"[LLM Router] Proveedor no soportado: {provider_type}")
                continue
            
            try:
                client = client_class(cfg)
                self.providers.append(client)
                
                # Cargar modelos disponibles para este proveedor
                model_info = get_model_by_id(provider_type, cfg.get('model', ''))
                if model_info:
                    self._provider_model_map[client.name] = [model_info]
                else:
                    self._provider_model_map[client.name] = []
                    
            except Exception as e:
                print(f"[LLM Router] Error inicializando {provider_type}: {e}")
    
    async def _is_rate_limited(self, provider_name: str) -> bool:
        """Verifica si un proveedor está en rate limit."""
        if provider_name in self._rate_limit_status:
            if asyncio.get_event_loop().time() < self._rate_limit_status[provider_name]:
                return True
            else:
                del self._rate_limit_status[provider_name]
        return False
    
    async def _set_rate_limited(self, provider_name: str, retry_after: int = 60):
        """Marca un proveedor como rate limited."""
        self._rate_limit_status[provider_name] = asyncio.get_event_loop().time() + retry_after
        print(f"[LLM Router] {provider_name} rate limitado por {retry_after}s")
    
    async def _get_available_provider(self) -> Optional[LLMClient]:
        """Obtiene el primer proveedor disponible en orden rotatorio."""
        async with self._lock:
            if not self.providers:
                return None
            
            # Probar desde el índice actual
            for i in range(len(self.providers)):
                idx = (self._current_index + i) % len(self.providers)
                provider = self.providers[idx]
                
                # Saltar si está rate limitado
                if await self._is_rate_limited(provider.name):
                    continue
                
                if await provider.available():
                    self._current_index = (idx + 1) % len(self.providers)
                    model_id = provider.model
                    print(f"[LLM Router] Usando: {provider.name} ({model_id})")
                    return provider
            
            # Si todos están rate limitados, esperar y reintentar
            if self._rate_limit_status:
                wait_time = max(0, max(self._rate_limit_status.values()) - asyncio.get_event_loop().time())
                if wait_time > 0:
                    print(f"[LLM Router] Todos los proveedores rate limitados. Esperando {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time + 1)
                    # Reintentar sin rate limits
                    for provider in self.providers:
                        if await provider.available():
                            return provider
            
            return None
    
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Genera respuesta usando el primer proveedor disponible."""
        max_attempts = len(self.providers) * 2  # Dos pasadas completas
        last_error = None
        
        for attempt in range(max_attempts):
            provider = await self._get_available_provider()
            if not provider:
                if last_error:
                    return f"Error: {last_error}"
                return "Error: No hay proveedores LLM disponibles"
            
            try:
                return await provider.generate(prompt, system_prompt, **kwargs)
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                print(f"[LLM Router] Error con {provider.name}: {error_msg}")
                
                # Detectar rate limits en los mensajes de error
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    await self._set_rate_limited(provider.name, 60)
                elif "404" in error_msg:
                    # Modelo no encontrado, marcar como no disponible
                    print(f"[LLM Router] Modelo {provider.model} no disponible en {provider.name}")
                    await self._set_rate_limited(provider.name, 300)  # 5 minutos
                else:
                    # Otro error, esperar un poco antes de reintentar
                    await asyncio.sleep(1)
        
        return f"Error después de {max_attempts} intentos: {last_error}"
    
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
                await asyncio.sleep(2 ** attempt)  # Backoff exponencial
        return f"Error después de {max_retries} intentos: {last_error}"
    
    def get_provider_models(self, provider_name: str) -> List[ProviderModel]:
        """Obtiene los modelos disponibles para un proveedor."""
        return self._provider_model_map.get(provider_name, [])
    
    def list_all_available_models(self) -> Dict[str, List[str]]:
        """Lista todos los modelos disponibles por proveedor."""
        result = {}
        for provider in self.providers:
            models = self.get_provider_models(provider.name)
            if models:
                result[provider.name] = [m.model_id for m in models]
            else:
                result[provider.name] = [provider.model]
        return result

__all__ = ['LLMRouter']
