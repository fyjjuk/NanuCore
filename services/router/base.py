"""
Clase base para routers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional

class BaseRouter(ABC):
    """Clase base para routers de intenciones."""
    
    @abstractmethod
    def route(self, routes: List[Dict[str, Any]], user_input: str, 
              threshold: Optional[float] = None) -> Tuple[str, float, Dict]:
        """
        Enruta una consulta a la ruta más adecuada.
        
        Args:
            routes: Lista de rutas disponibles
            user_input: Input del usuario
            threshold: Umbral de confianza mínimo
            
        Returns:
            Tuple con (route_id, confidence, intent)
        """
        pass
