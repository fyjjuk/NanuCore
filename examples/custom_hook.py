"""Ejemplo de hook personalizado para NanuCore."""
import logging
from typing import Dict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def audit_log_hook(user_input: str, context: Dict) -> str:
    """Registra todas las entradas del usuario con timestamp."""
    agent = context.get("agent")
    timestamp = datetime.now().isoformat()
    agent_name = agent.name if agent else "unknown"
    logger.info(f"[AUDIT] [{timestamp}] {agent_name}: {user_input[:100]}")
    return user_input


async def rate_limit_hook(user_input: str, context: Dict) -> str:
    """Ejemplo de hook para rate limiting (simplificado)."""
    session_key = context.get("session_key")
    if session_key:
        # Verificar límites aquí
        pass
    return user_input


async def translate_hook(response: str, context: Dict) -> str:
    """Hook que podría traducir la respuesta a otro idioma."""
    # Aquí iría lógica de traducción
    return response


async def error_notification_hook(error: Exception, user_input: str, context: Dict):
    """Hook que envía notificaciones de error."""
    logger.error(f"[ERROR HOOK] {error} | Input: {user_input[:50]}")


def register_hooks(pipeline):
    hook_manager = pipeline.get_hook_manager()
    hook_manager.add_pre_hook(audit_log_hook)
    hook_manager.add_pre_hook(rate_limit_hook)
    hook_manager.add_post_hook(translate_hook)
    hook_manager.add_error_hook(error_notification_hook)
    logger.info("✅ Hooks registrados")
