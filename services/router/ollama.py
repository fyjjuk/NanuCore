import requests
from typing import List, Dict, Any, Tuple, Optional
from core.logger import logger
from .base import BaseRouter

class OllamaRouter(BaseRouter):
    def __init__(self, model: str, threshold: float = 0.5, ollama_url: str = "http://localhost:11434/api/generate"):
        self.model = model
        self.threshold = threshold
        self.ollama_url = ollama_url

    def route(self, routes: List[Dict[str, Any]], user_input: str, threshold: Optional[float] = None) -> Tuple[str, float, Dict]:
        th = threshold if threshold is not None else self.threshold
        routes_desc = "\n".join([f"{r['route_id']}: {r.get('description', '')[:50]}" for r in routes])
        prompt = f"""Clasifica la consulta del usuario en una de estas rutas. Responde SOLO con el ID de la ruta.

Rutas:
{routes_desc}

Consulta: "{user_input}"

ID de la ruta:"""
        try:
            response = requests.post(
                self.ollama_url,
                json={"model": self.model, "prompt": prompt, "stream": False, "options": {"temperature": 0.0, "num_predict": 20}},
                timeout=15
            )
            raw = response.json().get("response", "").strip().lower()
            for route in routes:
                if route["route_id"].lower() == raw:
                    logger.info(f"OllamaRouter: {route['route_id']}")
                    return route["route_id"], 1.0, route
            return None, 0.0, None
        except Exception as e:
            logger.debug(f"OllamaRouter falló: {e}")
            return None, 0.0, None
