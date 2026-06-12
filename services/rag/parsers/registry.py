"""
Registry for document parsers.
Allows dynamic registration of new parsers.
"""

from typing import Dict, Type, Optional, List
from core.logger import logger


class ParserRegistry:
    """Registro central de parsers de documentos."""
    
    _instance = None
    _parsers: Dict[str, Type] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._parsers = {}
        return cls._instance
    
    def register(self, name: str, parser_class: Type, extensions: List[str] = None):
        """
        Registra un parser en el sistema.
        
        Args:
            name: Nombre único del parser
            parser_class: Clase del parser (debe tener método parse_file)
            extensions: Lista de extensiones que maneja
        """
        self._parsers[name] = {
            'class': parser_class,
            'extensions': extensions or []
        }
        logger.info(f"Parser registrado: {name} (extensiones: {extensions})")
    
    def get_parser(self, file_path: str) -> Optional[Type]:
        """
        Obtiene el parser adecuado para un archivo.
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Clase del parser o None si no hay match
        """
        import os
        ext = os.path.splitext(file_path)[1].lower()
        
        for name, info in self._parsers.items():
            if ext in info['extensions']:
                return info['class']
        
        return None
    
    def get_all_parsers(self) -> Dict:
        """Retorna todos los parsers registrados."""
        return self._parsers.copy()


# Singleton instance
parser_registry = ParserRegistry()


def register_parser(name: str, extensions: List[str] = None):
    """Decorador para registrar parsers automáticamente."""
    def decorator(parser_class):
        parser_registry.register(name, parser_class, extensions)
        return parser_class
    return decorator
