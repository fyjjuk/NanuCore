"""Clase base para canales de comunicación."""
from abc import ABC, abstractmethod
from typing import Optional
from nanu.core.orchestrator import Orchestrator

class Channel(ABC):
    """Canal de comunicación que envía y recibe mensajes."""
    
    def __init__(self, orchestrator: Orchestrator, agent_id: Optional[str] = None):
        self.orchestrator = orchestrator
        self.agent_id = agent_id  # Agente por defecto (None = usar selector)
        self._running = False
    
    @abstractmethod
    async def start(self) -> None:
        """Inicia el canal (bloqueante o en bucle)."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Detiene el canal."""
        pass
    
    async def _process_message(self, message: str, session_key: str) -> str:
        """Procesa un mensaje usando el pipeline del agente."""
        # Seleccionar agente si no está fijo
        if self.agent_id:
            agent = self.orchestrator.get_agent(self.agent_id)
            if not agent:
                return f"Error: Agente '{self.agent_id}' no encontrado"
        else:
            # Usar selector interactivo (solo para CLI)
            agent = await self.orchestrator.select_agent_interactive()
            if not agent:
                return "No se seleccionó agente"
        
        from nanu.core.pipeline import Pipeline
        pipeline = Pipeline(event_bus=self.orchestrator.event_bus)
        response, _ = await pipeline.run(agent, message, session_key)
        return response
