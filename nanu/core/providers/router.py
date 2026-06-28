"""Router de LLM con prioridad, fallback, rate limiting y selección inteligente de modelos."""
import asyncio
import time
from typing import List, Dict, Any, Optional

from nanu.core.logging import get_logger

from .base import LLMClient
from .ollama import OllamaClient
from .gemini import GeminiClient
from .groq import GroqClient
from .openrouter import OpenRouterClient
from .cerebras import CerebrasClient
from .mistral import MistralClient
from .huggingface import HuggingFaceClient
from .models import get_model_by_id, ProviderModel

# Logger para este módulo
logger = get_logger(__name__)


class LLMRouter:
    """Enruta solicitudes a múltiples proveedores LLM con prioridad y fallback."""
    
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
        self._provider_priority: Dict[str, int] = {}      # name -> priority (menor = mayor prioridad)
        self._provider_model_map: Dict[str, List[ProviderModel]] = {}
        self._rate_limit_status: Dict[str, float] = {}    # name -> timestamp de expiración
        self._failure_count: Dict[str, int] = {}          # name -> fallos consecutivos
        self._availability_cache: Dict[str, tuple] = {}   # name -> (timestamp, disponible)
        self._cache_ttl: int = 30                         # segundos
        self._failure_threshold: int = 3                  # fallos consecutivos para marcar como no disponible
        self._lock = asyncio.Lock()
        
        # Inicializar proveedores
        for cfg in providers_config:
            provider_type = cfg.get('type', 'ollama').lower()
            client_class = self.PROVIDER_CLASSES.get(provider_type)
            
            if not client_class:
                logger.warning(f"Proveedor no soportado: {provider_type}")
                continue
            
            try:
                client = client_class(cfg)
                self.providers.append(client)
                
                # Guardar prioridad (por defecto 999 = baja prioridad)
                priority = cfg.get('priority', 999)
                self._provider_priority[client.name] = priority
                
                # Cargar modelos disponibles para este proveedor
                model_info = get_model_by_id(provider_type, cfg.get('model', ''))
                if model_info:
                    self._provider_model_map[client.name] = [model_info]
                else:
                    self._provider_model_map[client.name] = []
                    
            except Exception as e:
                logger.error(f"Error inicializando {provider_type}: {e}")
        
        # Ordenar proveedores por prioridad (menor número = mayor prioridad)
        self.providers.sort(key=lambda p: self._provider_priority.get(p.name, 999))
        logger.info(f"Proveedores inicializados: {[p.name for p in self.providers]}")
        for p in self.providers:
            logger.debug(f"  - {p.name} (prioridad: {self._provider_priority.get(p.name, 999)})")
    
    async def _is_rate_limited(self, provider_name: str) -> bool:
        """Verifica si un proveedor está en rate limit."""
        if provider_name in self._rate_limit_status:
            if asyncio.get_event_loop().time() < self._rate_limit_status[provider_name]: 
                logger.debug(f"{provider_name} está rate limitado hasta {self._rate_limit_status[provider_name]}")
                return True
            else:
                del self._rate_limit_status[provider_name]
                logger.debug(f"{provider_name} ya no está rate limitado")
        return False
    
    async def _set_rate_limited(self, provider_name: str, retry_after: int = 60):
        """Marca un proveedor como rate limited."""
        self._rate_limit_status[provider_name] = asyncio.get_event_loop().time() + retry_after
        logger.warning(f"{provider_name} rate limitado por {retry_after}s")
    
    async def _is_provider_available(self, provider: LLMClient) -> bool:
        """Verifica disponibilidad de un proveedor con caché."""
        now = time.time()
        cache_entry = self._availability_cache.get(provider.name)
        
        if cache_entry:
            ts, available = cache_entry
            if now - ts < self._cache_ttl:
                logger.debug(f"{provider.name} disponible (caché): {available}")
                return available
        
        # Verificar disponibilidad real
        try:
            available = await provider.available()
            self._availability_cache[provider.name] = (now, available)
            logger.debug(f"{provider.name} disponible: {available}")
            return available
        except Exception as e:
            logger.error(f"Error verificando disponibilidad de {provider.name}: {e}")
            self._availability_cache[provider.name] = (now, False)
            return False
    
    async def _get_available_provider(self) -> Optional[LLMClient]:
        """Obtiene el proveedor con mayor prioridad disponible."""
        async with self._lock:
            if not self.providers:
                logger.error("No hay proveedores configurados")
                return None
            
            # Recorrer proveedores en orden de prioridad
            for provider in self.providers:
                provider_name = provider.name
                logger.debug(f"Evaluando {provider_name} (prioridad: {self._provider_priority.get(provider_name, 999)})")
                
                # Saltar si está rate limitado
                if await self._is_rate_limited(provider_name):
                    logger.debug(f"{provider_name} rate limitado, saltando")
                    continue
                
                # Saltar si ha tenido demasiados fallos consecutivos
                failures = self._failure_count.get(provider_name, 0)
                if failures >= self._failure_threshold:
                    logger.debug(f"{provider_name} tiene {failures} fallos consecutivos, saltando")
                    continue
                
                # Verificar disponibilidad
                if await self._is_provider_available(provider):
                    # Resetear contador de fallos en éxito
                    self._failure_count[provider_name] = 0
                    priority = self._provider_priority.get(provider_name, 999)
                    logger.info(f"Usando: {provider_name} (prioridad: {priority})")
                    return provider
                else:
                    # Incrementar contador de fallos
                    current = self._failure_count.get(provider_name, 0) + 1
                    self._failure_count[provider_name] = current
                    logger.debug(f"{provider_name} no disponible, fallos consecutivos: {current}")
            
            # Si todos están rate limitados o fallaron, esperar y reintentar
            if self._rate_limit_status:
                wait_time = max(0, max(self._rate_limit_status.values()) - asyncio.get_event_loop().time())
                if wait_time > 0:
                    logger.warning(f"Todos los proveedores rate limitados. Esperando {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time + 1)
                    # Reintentar sin rate limits
                    for provider in self.providers:
                        if await self._is_provider_available(provider):
                            return provider
            
            # Si algún proveedor tiene fallos, resetear después de un tiempo
            # (implementación simplificada)
            
            logger.error("No se encontró ningún proveedor disponible")
            return None
    
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Genera respuesta usando el primer proveedor disponible."""
        max_attempts = len(self.providers) * 2
        last_error = None
        
        for attempt in range(max_attempts):
            provider = await self._get_available_provider()
            if not provider:
                if last_error:
                    return f"Error: {last_error}"
                return "Error: No hay proveedores LLM disponibles"
            
            try:
                response = await provider.generate(prompt, system_prompt, **kwargs)
                # Si la respuesta contiene un error conocido, reintentar
                if "Error:" in response and "rate limit" in response.lower():
                    logger.warning(f"Rate limit detectado en respuesta de {provider.name}, marcando...")
                    await self._set_rate_limited(provider.name, 60)
                    continue
                return response
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                logger.error(f"Error con {provider.name}: {error_msg}")
                
                # Detectar rate limits
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    await self._set_rate_limited(provider.name, 60)
                elif "404" in error_msg:
                    logger.warning(f"Modelo {provider.model} no disponible en {provider.name}")
                    await self._set_rate_limited(provider.name, 300)
                else:
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
                logger.warning(f"Intento {attempt + 1} falló: {e}")
                await asyncio.sleep(2 ** attempt)
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
    
    def get_provider_priority(self, provider_name: str) -> int:
        """Obtiene la prioridad de un proveedor."""
        return self._provider_priority.get(provider_name, 999)
    
    def set_provider_priority(self, provider_name: str, priority: int):
        """Establece la prioridad de un proveedor en tiempo de ejecución."""
        self._provider_priority[provider_name] = priority
        # Reordenar proveedores
        self.providers.sort(key=lambda p: self._provider_priority.get(p.name, 999))
        logger.info(f"Prioridad de {provider_name} actualizada a {priority}")

__all__ = ['LLMRouter']
