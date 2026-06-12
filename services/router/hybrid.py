from typing import List, Dict, Any, Tuple, Optional
from core.logger import logger
from .base import BaseRouter
from .embedding import EmbeddingRouter
from .ollama import OllamaRouter

class HybridRouter(BaseRouter):
    def __init__(self, embedding_threshold: float = 0.7, ollama_model: str = "phi3:mini", fallback_threshold: float = 0.3):
        self.embedding = EmbeddingRouter(threshold=embedding_threshold)
        self.ollama = OllamaRouter(model=ollama_model)
        self.fallback_threshold = fallback_threshold

    def route(self, routes: List[Dict[str, Any]], user_input: str, threshold: Optional[float] = None) -> Tuple[str, float, Dict]:
        # 1. Intentar embedding primero
        route_id, score, route = self.embedding.route(routes, user_input)
        
        # 2. Si embedding encontró una ruta con alta confianza
        if route_id and score >= self.embedding.threshold:
            logger.info(f"HybridRouter: embedding alta confianza: {route_id} (score={score:.2f})")
            return route_id, score, route
        
        # 3. Si embedding encontró algo pero con confianza baja, o no encontró nada
        #    Usar Ollama como respaldo
        logger.info(f"HybridRouter: embedding score={score:.2f}, usando Ollama")
        ollama_id, ollama_score, ollama_route = self.ollama.route(routes, user_input)
        
        if ollama_id:
            logger.info(f"HybridRouter: Ollama seleccionó: {ollama_id}")
            return ollama_id, ollama_score, ollama_route
        
        # 4. Fallback final
        if route:
            return route_id, score, route
        return None, 0.0, None
