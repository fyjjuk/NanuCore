"""Interfaz base para plugins de utilidad."""
from abc import ABC, abstractmethod

class UtilityPlugin(ABC):
    """Clase base para todas las utilidades (plugins)."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre legible del plugin."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Breve descripción de lo que hace el plugin."""
        pass
    
    @property
    @abstractmethod
    def category(self) -> str:
        """Categoría del plugin (diagnostic, user, shell, cli, repomix)."""
        pass
    
    @abstractmethod
    def run(self) -> None:
        """Ejecuta la funcionalidad del plugin."""
        pass
