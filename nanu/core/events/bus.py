"""Bus de eventos asíncrono con suscripciones."""
import asyncio
from typing import Dict, List, Callable, Awaitable, Any

class EventBus:
    """Implementación simple de un bus de eventos asíncrono."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], Awaitable[None]]]] = {}
    
    def subscribe(self, event: str, handler: Callable[[Any], Awaitable[None]]) -> None:
        """Registra un handler para un evento."""
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(handler)
    
    async def publish(self, event: str, data: Any) -> None:
        """Publica un evento a todos los handlers suscritos."""
        if event not in self._subscribers:
            return
        handlers = self._subscribers[event]
        # Llamar a todos los handlers en paralelo (no esperar a cada uno)
        await asyncio.gather(*[handler(data) for handler in handlers], return_exceptions=True)
    
    def unsubscribe(self, event: str, handler: Callable[[Any], Awaitable[None]]) -> None:
        """Elimina un handler específico."""
        if event in self._subscribers:
            self._subscribers[event] = [h for h in self._subscribers[event] if h != handler]
