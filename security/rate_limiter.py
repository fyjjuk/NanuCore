import time
from collections import defaultdict
from typing import Optional
from core.logger import logger

class RateLimiter:
    """Rate limiter simple basado en ventana deslizante."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)
    
    def is_allowed(self, user_id: str) -> bool:
        """Verifica si el usuario puede realizar una nueva solicitud."""
        now = time.time()
        
        # Limpiar solicitudes antiguas
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.window_seconds
        ]
        
        if len(self.requests[user_id]) >= self.max_requests:
            logger.warning(f"Rate limit excedido para usuario {user_id}")
            return False
        
        self.requests[user_id].append(now)
        return True
    
    def get_remaining(self, user_id: str) -> int:
        """Devuelve cuántas solicitudes quedan en la ventana actual."""
        now = time.time()
        recent = [
            req_time for req_time in self.requests.get(user_id, [])
            if now - req_time < self.window_seconds
        ]
        return max(0, self.max_requests - len(recent))
    
    def reset(self, user_id: str) -> None:
        """Resetea el contador para un usuario."""
        if user_id in self.requests:
            del self.requests[user_id]
