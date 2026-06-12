"""Interfaces y protocolos para el núcleo de NanuCore."""
from typing import Protocol, Dict, Any, AsyncIterator, Optional, List
from abc import ABC, abstractmethod

class LLMClient(Protocol):
    """Protocolo para clientes de LLM (asíncrono)."""
    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        ...
    async def stream(self, prompt: str, system: str = "", **kwargs) -> AsyncIterator[str]:
        ...

class Tool(ABC):
    """Clase base para herramientas del agente."""
    name: str
    description: str
    enabled: bool = True

    @abstractmethod
    async def execute(self, args: Dict[str, Any], workspace: Optional[str] = None) -> str:
        """Ejecuta la herramienta con los argumentos dados."""
        ...

class MemoryStore(Protocol):
    """Protocolo para almacenamiento de historial de conversación."""
    async def add(self, session_key: str, turn: Dict[str, Any]) -> None:
        ...
    async def get_history(self, session_key: str, limit: int = 10) -> List[Dict[str, Any]]:
        ...
    async def clear(self, session_key: str) -> None:
        ...

class VectorStore(Protocol):
    """Protocolo para búsqueda semántica (RAG ligero)."""
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        ...
    async def index(self, doc_id: str, content: str, metadata: Dict[str, Any]) -> None:
        ...
    async def delete_namespace(self, namespace: str) -> None:
        ...

class EventBus(Protocol):
    """Protocolo para bus de eventos asíncrono."""
    async def publish(self, event: str, data: Any) -> None:
        ...
    def subscribe(self, event: str, handler) -> None:
        ...
