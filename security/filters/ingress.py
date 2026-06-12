import re
import logging
from typing import Dict, Any
from security.rate_limiter import RateLimiter

logger = logging.getLogger("ferdonan.firewall.ingress")

class IngressFilter:
    def __init__(self, global_regex_path: str, layer2_model_name: str = None, enabled_layer2: bool = False):
        self.enabled_layer2 = enabled_layer2
        self.global_regex = self._load_regex_blacklist(global_regex_path)
        self.classifier = None
        self.rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
        
        if self.enabled_layer2:
            logger.warning("Capa 2 semántica no disponible - ejecutando solo con Capa 1 (RegEx)")

    def _load_regex_blacklist(self, path: str) -> list:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except Exception as e:
            logger.error(f"Error cargando blacklist RegEx global: {str(e)}")
            return []

    def evaluate(self, user_input: str, agent) -> bool:
        # Obtener ID del agente (puede ser objeto o dict por compatibilidad)
        if hasattr(agent, 'id'):
            user_id = agent.id
            firewall_override = getattr(agent, 'firewall_override', {})
        else:
            # Fallback por si se pasa dict (compatibilidad)
            user_id = agent.get("id", "default")
            firewall_override = agent.get("firewall_override", {})
        
        # Rate limiting
        if not self.rate_limiter.is_allowed(user_id):
            logger.error(f"Rate limit excedido para {user_id}")
            return False
        
        # CAPA 1: RegEx Determinista
        agent_blacklist = firewall_override.get("ingress", {}).get("layer1_regex", {}).get("blacklist", [])
        full_blacklist = self.global_regex + agent_blacklist

        for pattern in full_blacklist:
            if re.search(pattern, user_input, re.IGNORECASE):
                logger.error(f"INPUT BLOQUEADO por Capa 1 (RegEx). Patrón: {pattern}")
                return False

        # CAPA 2: Desactivada por ahora
        if self.enabled_layer2 and self.classifier:
            try:
                prediction = self.classifier(user_input)[0]
                if prediction['label'] == 'LABEL_1' and prediction['score'] > 0.85:
                    logger.error(f"INPUT BLOQUEADO por Capa 2 (Semántica)")
                    return False
            except Exception as e:
                logger.critical(f"Error en Capa 2: {str(e)}. Aplicando Fail-Closed.")
                return False

        logger.info("Input verificado por IngressFilter.")
        return True
