from services.router.intent_router import Router
from services.sanitizer.input_cleaner import Sanitizer

def create_router(agent) -> Router:
    """Crea un router basado en la configuración del agente."""
    cfg = agent.router_config
    return Router(mode=cfg.mode, model=cfg.model, threshold=cfg.threshold)

def create_sanitizer(agent) -> Sanitizer:
    """Crea un sanitizador basado en la configuración del agente."""
    cfg = agent.sanitizer_config
    return Sanitizer(enabled=cfg.enabled, model=cfg.model)
