"""
Interfaces estandarizadas para el sistema FerdoNAN.
Utiliza Protocol para duck typing y ABC para herencia explícita.
"""

from typing import Protocol, Dict, Any, Optional, List, Tuple, runtime_checkable
from abc import ABC, abstractmethod


# ============================================================================
# LLM Providers
# ============================================================================

class LLMClientInterface(Protocol):
    """Interfaz para clientes de LLM (Ollama, Gemini, Groq, Local)."""
    
    def generate_response(self, prompt: str, system_prompt: str, config: Dict[str, Any]) -> str:
        """Genera una respuesta del LLM."""
        ...
    
    def stream_response(self, prompt: str, system_prompt: str, config: Dict[str, Any]):
        """Genera respuesta con streaming (opcional)."""
        ...


# ============================================================================
# RAG (Retrieval-Augmented Generation)
# ============================================================================

class RAGEngineInterface(Protocol):
    """Interfaz para el motor RAG."""
    
    def index_document(self, agent_id: str, content: str, metadata: Dict[str, Any]) -> Optional[str]:
        """Indexa un documento en la colección del agente."""
        ...
    
    def rag_query(self, agent_id: str, query_text: str, top_k: int = 5, 
                  similarity_threshold: float = 0.75) -> Dict[str, Any]:
        """Realiza una consulta RAG."""
        ...
    
    def delete_namespace(self, agent_id: str) -> None:
        """Elimina toda la colección de un agente."""
        ...


# ============================================================================
# Cache
# ============================================================================

class CacheInterface(Protocol):
    """Interfaz para el sistema de caché."""
    
    def get(self, agent_id: str, route_id: str, input_text: str) -> Optional[str]:
        """Obtiene una respuesta cacheadas."""
        ...
    
    def set(self, agent_id: str, route_id: str, input_text: str, output: str) -> None:
        """Almacena una respuesta en caché."""
        ...
    
    def invalidate(self, agent_id: str, route_id: Optional[str] = None) -> None:
        """Invalida caché para un agente o ruta específica."""
        ...


# ============================================================================
# Gatekeeper (Autorización humana)
# ============================================================================

class GatekeeperInterface(Protocol):
    """Interfaz para el Gatekeeper (aprobación humana)."""
    
    def verify(self, route_id: str, route_config: dict, request_id: str) -> bool:
        """Verifica si una ruta está aprobada para ejecución."""
        ...
    
    def reset_session_cache(self, route_id: Optional[str] = None) -> None:
        """Resetea el caché de decisiones de sesión."""
        ...


# ============================================================================
# Memory (Corto y Largo Plazo)
# ============================================================================

class ShortTermMemoryInterface(Protocol):
    """Interfaz para memoria a corto plazo."""
    
    def add(self, agent_id: str, user_input: str, assistant_output: str) -> None:
        """Añade un turno de conversación a la memoria."""
        ...
    
    def get_context(self, agent_id: str, n_turns: int = 5) -> List[Dict[str, str]]:
        """Obtiene los últimos N turnos de conversación."""
        ...
    
    def clear(self, agent_id: str) -> None:
        """Limpia la memoria del agente."""
        ...


class LongTermMemoryInterface(Protocol):
    """Interfaz para memoria a largo plazo."""
    
    def store(self, agent_id: str, key: str, value: Any, metadata: Optional[Dict] = None) -> None:
        """Almacena información persistente."""
        ...
    
    def retrieve(self, agent_id: str, key: str) -> Optional[Any]:
        """Recupera información persistente."""
        ...
    
    def search(self, agent_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca información por similitud semántica."""
        ...


# ============================================================================
# Router (Enrutamiento de intenciones)
# ============================================================================

class RouterInterface(Protocol):
    """Interfaz para el enrutador de intenciones."""
    
    def route(self, agent_id: str, user_input: str, 
              threshold: Optional[float] = None) -> Tuple[str, float, Dict[str, Any]]:
        """Enruta una consulta a la ruta más adecuada."""
        ...
    
    def needs_rag_context(self, query: str, agent) -> bool:
        """Determina si se necesita contexto RAG."""
        ...


# ============================================================================
# Executor (Ejecutores de rutas)
# ============================================================================

class ExecutorInterface(Protocol):
    """Interfaz para ejecutores de rutas."""
    
    def execute(self, agent, intent: Dict[str, Any], 
                query: str, router, rag_engine) -> str:
        """Ejecuta una ruta y retorna la respuesta."""
        ...


# ============================================================================
# Sanitizer (Limpieza de inputs)
# ============================================================================

class SanitizerInterface(Protocol):
    """Interfaz para sanitizadores de entrada."""
    
    def clean(self, user_input: str) -> str:
        """Limpia el input del usuario."""
        ...


# ============================================================================
# Clases base abstractas (para herencia)
# ============================================================================

class BaseLLMClient(ABC):
    """Clase base abstracta para clientes LLM."""
    
    @abstractmethod
    def generate_response(self, prompt: str, system_prompt: str, config: Dict[str, Any]) -> str:
        """Genera una respuesta del LLM."""
        pass
    
    @abstractmethod
    def stream_response(self, prompt: str, system_prompt: str, config: Dict[str, Any]):
        """Genera respuesta con streaming."""
        pass


class BaseCache(ABC):
    """Clase base abstracta para caché."""
    
    @abstractmethod
    def get(self, agent_id: str, route_id: str, input_text: str) -> Optional[str]:
        pass
    
    @abstractmethod
    def set(self, agent_id: str, route_id: str, input_text: str, output: str) -> None:
        pass


class BaseGatekeeper(ABC):
    """Clase base abstracta para Gatekeeper."""
    
    @abstractmethod
    def verify(self, route_id: str, route_config: dict, request_id: str) -> bool:
        pass


__all__ = [
    # Protocols
    'LLMClientInterface',
    'RAGEngineInterface', 
    'CacheInterface',
    'GatekeeperInterface',
    'ShortTermMemoryInterface',
    'LongTermMemoryInterface',
    'RouterInterface',
    'ExecutorInterface',
    'SanitizerInterface',
    # Abstract Base Classes
    'BaseLLMClient',
    'BaseCache',
    'BaseGatekeeper',
]

# ============================================================================
# UI Renderer (Desacoplado)
# ============================================================================

class UIRendererInterface(Protocol):
    """Interfaz para el renderizador de UI (consola, web, etc.)"""
    
    def render_info(self, message: str, **kwargs) -> str:
        """Renderiza mensaje informativo."""
        ...
    
    def render_success(self, message: str, **kwargs) -> str:
        """Renderiza mensaje de éxito."""
        ...
    
    def render_error(self, message: str, **kwargs) -> str:
        """Renderiza mensaje de error."""
        ...
    
    def render_warning(self, message: str, **kwargs) -> str:
        """Renderiza mensaje de advertencia."""
        ...
    
    def render_badge(self, text: str, style: str = "default", **kwargs) -> str:
        """Renderiza un badge estilizado."""
        ...
    
    def render_table(self, headers: list, rows: list, **kwargs) -> str:
        """Renderiza una tabla."""
        ...
    
    def render_progress(self, current: int, total: int, **kwargs) -> str:
        """Renderiza barra de progreso."""
        ...
