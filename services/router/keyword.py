import re
from typing import List, Dict, Any, Tuple, Optional
from core.logger import logger
from .base import BaseRouter

class KeywordRouter(BaseRouter):
    def __init__(self, threshold: float = 0.3):
        self.threshold = threshold

    def route(self, routes: List[Dict[str, Any]], user_input: str, threshold: Optional[float] = None) -> Tuple[str, float, Dict]:
        th = threshold if threshold is not None else self.threshold
        user_lower = user_input.lower()
        best_match = None
        best_score = 0.0
        for route in routes:
            desc = route.get("description", "").lower()
            keywords = re.split(r'[, ]+', desc)
            matches = sum(1 for kw in keywords if kw and kw in user_lower)
            if matches > 0:
                score = matches / len(keywords) if keywords else 0
                if score > best_score:
                    best_score = score
                    best_match = route
        if best_match and best_score >= th:
            logger.info(f"KeywordRouter: {best_match['route_id']} (score={best_score:.2f})")
            return best_match["route_id"], best_score, best_match
        return None, 0.0, None
