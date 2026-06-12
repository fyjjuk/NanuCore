"""Sistema de hooks para el pipeline de NanuCore."""
from typing import Dict, Any, Callable, Awaitable, Optional, List
import asyncio
import logging

logger = logging.getLogger(__name__)

class HookManager:
    """Gestiona hooks que se ejecutan en diferentes puntos del pipeline."""
    
    def __init__(self):
        self.pre_process_hooks: List[Callable[[str, Dict], Awaitable[str]]] = []
        self.post_process_hooks: List[Callable[[str, Dict], Awaitable[str]]] = []
        self.on_error_hooks: List[Callable[[Exception, str, Dict], Awaitable[None]]] = []
        self.pre_route_hooks: List[Callable[[str, Dict], Awaitable[str]]] = []
        self.post_route_hooks: List[Callable[[str, str, Dict], Awaitable[str]]] = []
    
    def add_pre_hook(self, hook: Callable[[str, Dict], Awaitable[str]]):
        """Hook ejecutado antes de sanitizar el input."""
        self.pre_process_hooks.append(hook)
    
    def add_post_hook(self, hook: Callable[[str, Dict], Awaitable[str]]):
        """Hook ejecutado después de generar la respuesta (antes de egress)."""
        self.post_process_hooks.append(hook)
    
    def add_error_hook(self, hook: Callable[[Exception, str, Dict], Awaitable[None]]):
        """Hook ejecutado cuando ocurre una excepción en el pipeline."""
        self.on_error_hooks.append(hook)
    
    def add_pre_route_hook(self, hook: Callable[[str, Dict], Awaitable[str]]):
        """Hook ejecutado antes del enrutamiento (sobre el input sanitizado)."""
        self.pre_route_hooks.append(hook)
    
    def add_post_route_hook(self, hook: Callable[[str, str, Dict], Awaitable[str]]):
        """Hook ejecutado después del enrutamiento (recibe route_id y input)."""
        self.post_route_hooks.append(hook)
    
    async def run_pre_hooks(self, user_input: str, context: Dict) -> str:
        """Ejecuta todos los pre-process hooks."""
        result = user_input
        for hook in self.pre_process_hooks:
            try:
                result = await hook(result, context)
            except Exception as e:
                logger.error(f"Error en pre hook: {e}")
        return result
    
    async def run_pre_route_hooks(self, user_input: str, context: Dict) -> str:
        """Ejecuta hooks antes del enrutamiento."""
        result = user_input
        for hook in self.pre_route_hooks:
            try:
                result = await hook(result, context)
            except Exception as e:
                logger.error(f"Error en pre-route hook: {e}")
        return result
    
    async def run_post_route_hooks(self, route_id: str, user_input: str, context: Dict) -> str:
        """Ejecuta hooks después del enrutamiento."""
        result = user_input
        for hook in self.post_route_hooks:
            try:
                result = await hook(route_id, result, context)
            except Exception as e:
                logger.error(f"Error en post-route hook: {e}")
        return result
    
    async def run_post_hooks(self, response: str, context: Dict) -> str:
        """Ejecuta todos los post-process hooks."""
        result = response
        for hook in self.post_process_hooks:
            try:
                result = await hook(result, context)
            except Exception as e:
                logger.error(f"Error en post hook: {e}")
        return result
    
    async def run_error_hooks(self, error: Exception, user_input: str, context: Dict):
        """Ejecuta todos los error hooks."""
        for hook in self.on_error_hooks:
            try:
                await hook(error, user_input, context)
            except Exception as e:
                logger.error(f"Error en error hook: {e}")
