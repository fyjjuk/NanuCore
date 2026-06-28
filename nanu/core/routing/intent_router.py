from pathlib import Path
import re
import yaml
from typing import Dict, Any, Optional
from nanu.core.agent import Agent
from nanu.core.logging import get_logger

logger = get_logger(__name__)

class IntentRouter:
    def route(self, agent: Agent, user_input: str, threshold: float = 0.05) -> Optional[Dict[str, Any]]:
        user_lower = user_input.lower().strip()
        best_route = None
        best_score = 0.0
        
        routes_dir = Path(agent.config_path).parent / "routes"
        if not routes_dir.exists():
            logger.debug(f"No hay directorio de rutas para {agent.id}")
            return None
        
        for yaml_file in routes_dir.glob("*.yaml"):
            with open(yaml_file, 'r', encoding='utf-8') as f:
                route = yaml.safe_load(f)
                if not route or 'route_id' not in route:
                    continue
                desc = route.get('description', '').lower()
                keywords = re.split(r'[, ]+', desc)
                matches = 0
                for kw in keywords:
                    if kw and kw in user_lower:
                        matches += 1
                        if kw == user_lower:
                            matches += 0.3
                if matches > 0:
                    score = matches / (len(keywords) + 0.3)
                    if score > best_score:
                        best_score = score
                        best_route = route
        
        if best_route and best_score >= threshold:
            logger.debug(f"Ruta seleccionada: {best_route['route_id']} (score={best_score:.2f})")
            return best_route
        
        # Fallback: si no hay match, usar primera ruta (comando) solo si el input no es vacío
        if user_lower and routes_dir.exists():
            # Buscar ruta "comando" como fallback
            for yaml_file in routes_dir.glob("*.yaml"):
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    route = yaml.safe_load(f)
                    if route and route.get('route_id') == 'comando':
                        logger.debug(f"Fallback a comando (input: '{user_lower}')")
                        return route
        
        logger.debug(f"No se encontró ruta para: '{user_input}'")
        return None
