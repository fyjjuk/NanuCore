from typing import List, Dict, Any, Tuple, Optional
from sentence_transformers import SentenceTransformer, util
from core.logger import logger
from .base import BaseRouter

class EmbeddingRouter(BaseRouter):
    def __init__(self, threshold: float = 0.5, model_name: str = 'all-MiniLM-L6-v2'):
        self.threshold = threshold
        self.model = SentenceTransformer(model_name)

    def route(self, routes: List[Dict[str, Any]], user_input: str, threshold: Optional[float] = None) -> Tuple[str, float, Dict]:
        th = threshold if threshold is not None else self.threshold
        route_texts = [f"{r['route_id']}: {r.get('description', '')}" for r in routes]
        route_embeds = self.model.encode(route_texts, convert_to_tensor=True)
        input_embed = self.model.encode(user_input, convert_to_tensor=True)
        scores = util.cos_sim(input_embed, route_embeds)[0]
        best_idx = int(scores.argmax())
        best_score = float(scores[best_idx])
        best_route = routes[best_idx]
        if best_score >= th:
            logger.info(f"EmbeddingRouter: {best_route['route_id']} (score={best_score:.2f})")
            return best_route["route_id"], best_score, best_route
        return None, best_score, None
