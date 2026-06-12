import os
import yaml
from typing import List, Dict, Any, Tuple, Optional
from core.logger import logger
from services.router.factory import create_router
from models.intent_models import validate_route

class RouteNotFoundError(Exception):
    def __init__(self, message: str, available_routes: List[Dict[str, Any]]):
        super().__init__(message)
        self.available_routes = available_routes

class Router:
    def __init__(self, mode: str = "keyword", model: Optional[str] = None, threshold: float = 0.3):
        self._config = {"mode": mode, "model": model, "threshold": threshold}
        self._router = create_router(self._config)

    def _load_agent_routes(self, agent_id: str) -> List[Dict[str, Any]]:
        routes_dir = os.path.join("agents", agent_id, "routes")
        routes = []
        invalid_count = 0
        if not os.path.exists(routes_dir):
            return routes
        for filename in os.listdir(routes_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(routes_dir, filename)
                with open(filepath, "r") as f:
                    intent = yaml.safe_load(f)
                    if intent and "route_id" in intent:
                        # Validar esquema
                        is_valid, model, errors = validate_route(intent)
                        if is_valid:
                            routes.append(intent)
                        else:
                            invalid_count += 1
                            print(f"\033[93m⚠️ Ruta inválida en {agent_id}/{filename}: {intent.get('route_id', 'unknown')}\033[0m")
                            for error in errors[:3]:  # Mostrar hasta 3 errores
                                print(f"\033[91m   - {error}\033[0m")
                            logger.warning(f"Ruta inválida en {agent_id}/{filename}: {errors}")
                    elif intent:
                        print(f"\033[93m⚠️ Archivo {filename} no tiene 'route_id', omitido\033[0m")
        if invalid_count > 0:
            print(f"\033[93m⚠️ Agente {agent_id}: {invalid_count} rutas inválidas omitidas\033[0m")
        return routes

    def needs_rag_context(self, query: str, agent=None) -> bool:
        return agent.rag_config.enabled if agent and hasattr(agent, "rag_config") else False

    def route(self, agent_id: str, user_input: str, threshold: Optional[float] = None) -> Tuple[str, float, Dict]:
        routes = self._load_agent_routes(agent_id)
        if not routes:
            raise RouteNotFoundError("No hay rutas definidas para este agente.", [])
        result = self._router.route(routes, user_input, threshold)
        if result[0]:
            return result
        # Fallback a primera ruta
        default = routes[0]
        logger.debug(f"Usando ruta por defecto: {default['route_id']}")
        return default["route_id"], 0.5, default
