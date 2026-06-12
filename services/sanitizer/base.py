"""
Clase base para sanitizadores.
"""

from abc import ABC, abstractmethod

class BaseSanitizer(ABC):
    """Clase base para sanitizadores de entrada."""
    
    @abstractmethod
    def clean(self, user_input: str) -> str:
        """
        Limpia el input del usuario.
        
        Args:
            user_input: Texto de entrada del usuario
            
        Returns:
            str: Texto sanitizado
        """
        pass
