"""
MarkItDown parser adapter for RAG document ingestion.
Converts various document formats to markdown text.
"""

import os
from typing import Optional, Dict, Any
from core.logger import logger

try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False
    logger.warning("MarkItDown no está instalado. Instale con: pip install markitdown")


class MarkItDownParser:
    """Adapter para MarkItDown que convierte documentos a texto plano."""
    
    def __init__(self, llm_client=None, llm_model: Optional[str] = None):
        """
        Inicializa el parser de MarkItDown.
        
        Args:
            llm_client: Cliente LLM opcional para OCR avanzado
            llm_model: Modelo LLM para procesamiento adicional
        """
        if not MARKITDOWN_AVAILABLE:
            raise ImportError("MarkItDown is required. Install with: pip install markitdown")
        
        self.llm_client = llm_client
        self.llm_model = llm_model
        self._md = None
    
    @property
    def md(self):
        """Lazy initialization of MarkItDown instance."""
        if self._md is None:
            self._md = MarkItDown(
                llm_client=self.llm_client,
                llm_model=self.llm_model
            )
        return self._md
    
    def parse_file(self, file_path: str) -> Optional[str]:
        """
        Convierte un archivo a texto usando MarkItDown.
        
        Args:
            file_path: Ruta al archivo a convertir
            
        Returns:
            str: Texto extraído o None si error
        """
        if not os.path.exists(file_path):
            logger.error(f"Archivo no encontrado: {file_path}")
            return None
        
        try:
            result = self.md.convert(file_path)
            if result and hasattr(result, 'text_content'):
                text = result.text_content
                logger.info(f"MarkItDown: convertido {file_path} ({len(text)} caracteres)")
                return text
            elif result and isinstance(result, str):
                logger.info(f"MarkItDown: convertido {file_path} ({len(result)} caracteres)")
                return result
            else:
                logger.error(f"MarkItDown: resultado inesperado para {file_path}")
                return None
        except Exception as e:
            logger.error(f"Error convirtiendo {file_path} con MarkItDown: {e}")
            return None
    
    def parse_url(self, url: str) -> Optional[str]:
        """
        Convierte contenido de una URL a texto usando MarkItDown.
        
        Args:
            url: URL del contenido a convertir
            
        Returns:
            str: Texto extraído o None si error
        """
        try:
            result = self.md.convert_url(url)
            if result and hasattr(result, 'text_content'):
                return result.text_content
            elif result and isinstance(result, str):
                return result
            return None
        except Exception as e:
            logger.error(f"Error convirtiendo URL {url} con MarkItDown: {e}")
            return None
    
    def get_supported_extensions(self) -> list:
        """Retorna lista de extensiones de archivo soportadas."""
        # Extensiones soportadas por MarkItDown
        return [
            '.pdf', '.docx', '.xlsx', '.pptx', '.html', '.htm',
            '.md', '.txt', '.csv', '.json', '.xml', '.jpg', '.jpeg',
            '.png', '.gif', '.bmp', '.tiff'
        ]
    
    def can_handle(self, file_path: str) -> bool:
        """Verifica si el parser puede manejar este archivo."""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.get_supported_extensions()
