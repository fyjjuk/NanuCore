"""
Indexación de documentos para RAG con soporte para múltiples parsers.
"""

import os
import datetime
from typing import Dict, Any, Optional
from core.logger import logger
from .utils import generate_document_id, validate_agent_id
from .collection import CollectionManager
from .parsers.markitdown_parser import MarkItDownParser


class IndexingService:
    """Servicio para indexar documentos en RAG."""
    
    def __init__(self, collection_manager: CollectionManager, embedding_model):
        self.collection_manager = collection_manager
        self.model = embedding_model
        self.markitdown_parser = None
        
        # Inicializar MarkItDown si está disponible
        try:
            self.markitdown_parser = MarkItDownParser()
            logger.info("MarkItDown parser inicializado para indexación avanzada")
        except ImportError:
            logger.warning("MarkItDown no disponible. Usando parsers básicos.")
    
    def index_document(self, agent_id: str, content: str, metadata: Dict[str, Any]) -> Optional[str]:
        """Indexa un documento en la colección del agente."""
        if not validate_agent_id(agent_id):
            return None
        
        collection = self.collection_manager.get_collection(agent_id)
        if collection is None:
            return None
        
        embedding = self.model.encode(content).tolist()
        doc_id = generate_document_id(agent_id, content, metadata.get('timestamp', ''))
        
        collection.add(
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id]
        )
        logger.info(f"RAG_INDEX: Documento {doc_id} indexado en {agent_id}")
        return doc_id
    
    def index_conversation_turn(self, agent_id: str, user_msg: str, 
                                 assistant_msg: str, metadata: Optional[Dict] = None) -> Optional[str]:
        """Indexa un turno de conversación."""
        content = f"Usuario: {user_msg}\nAsistente: {assistant_msg}"
        meta = {"type": "conversation", "timestamp": datetime.datetime.now().isoformat()}
        if metadata:
            meta.update(metadata)
        return self.index_document(agent_id, content, meta)
    
    def process_and_index_file(self, agent_id: str, file_path: str, 
                                use_markitdown: bool = True) -> Optional[str]:
        """
        Procesa y indexa un archivo usando el parser más adecuado.
        
        Args:
            agent_id: Identificador del agente
            file_path: Ruta del archivo
            use_markitdown: Si usar MarkItDown para formatos complejos
            
        Returns:
            str: ID del documento indexado o None si error
        """
        if not os.path.exists(file_path):
            logger.error(f"Archivo no encontrado: {file_path}")
            return None
        
        ext = os.path.splitext(file_path)[1].lower()
        
        # Intentar con MarkItDown primero (soporta más formatos)
        if use_markitdown and self.markitdown_parser and self.markitdown_parser.can_handle(file_path):
            logger.info(f"Usando MarkItDown para procesar: {file_path}")
            text = self.markitdown_parser.parse_file(file_path)
            if text:
                metadata = {
                    "source": file_path,
                    "timestamp": str(os.path.getmtime(file_path)),
                    "parser": "markitdown"
                }
                return self.index_document(agent_id, text, metadata)
            else:
                logger.warning(f"MarkItDown falló para {file_path}, usando fallback")
        
        # Fallback: parsers básicos
        try:
            if ext == '.docx':
                import docx
                doc = docx.Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs])
            elif ext == '.xlsx':
                import pandas as pd
                df = pd.read_excel(file_path)
                text = df.to_string()
            elif ext == '.md' or ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            elif ext == '.pdf' and not use_markitdown:
                # PDF sin MarkItDown - intentar con PyPDF2
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = "\n".join([page.extract_text() for page in reader.pages])
                except ImportError:
                    logger.error("PyPDF2 no instalado para PDFs. Use: pip install PyPDF2")
                    return None
            else:
                if not self.markitdown_parser:
                    logger.warning(f"Formato no soportado: {ext}. MarkItDown no disponible.")
                    return None
                # Intentar igual con MarkItDown como último recurso
                if self.markitdown_parser:
                    text = self.markitdown_parser.parse_file(file_path)
                    if not text:
                        raise ValueError(f"Formato no soportado: {ext}")
                else:
                    raise ValueError(f"Formato no soportado: {ext}")
            
            metadata = {
                "source": file_path,
                "timestamp": str(os.path.getmtime(file_path)),
                "parser": "fallback"
            }
            return self.index_document(agent_id, text, metadata)
        except Exception as e:
            logger.error(f"Error procesando {file_path}: {e}")
            return None
    
    def parse_and_index_url(self, agent_id: str, url: str) -> Optional[str]:
        """
        Procesa y indexa contenido desde una URL usando MarkItDown.
        
        Args:
            agent_id: Identificador del agente
            url: URL del contenido
            
        Returns:
            str: ID del documento indexado o None si error
        """
        if not self.markitdown_parser:
            logger.error("MarkItDown requerido para procesar URLs")
            return None
        
        text = self.markitdown_parser.parse_url(url)
        if not text:
            return None
        
        metadata = {
            "source": url,
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "url",
            "parser": "markitdown"
        }
        return self.index_document(agent_id, text, metadata)
