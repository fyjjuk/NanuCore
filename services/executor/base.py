"""
Clase base para ejecutores de rutas.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseExecutor(ABC):
    """Clase base para todos los ejecutores."""
    
    @abstractmethod
    def execute(self, agent, intent: Dict[str, Any], 
                query: str, router, rag_engine) -> str:
        """
        Ejecuta una ruta y retorna la respuesta.
        
        Args:
            agent: Manifiesto del agente
            intent: Datos de la ruta
            query: Input sanitizado
            router: Router para determinar necesidades
            rag_engine: Motor RAG para contexto
            
        Returns:
            str: Respuesta generada
        """
        pass
