"""
RAG (Retrieval-Augmented Generation) module

Proporciona servicios para indexación y búsqueda semántica de documentos.
"""

from sentence_transformers import SentenceTransformer
from .collection import CollectionManager
from .indexing import IndexingService
from .query import QueryService
from .utils import validate_agent_id, sanitize_query, generate_document_id


class RAGEngine:
    """
    Motor RAG completo que integra colecciones, indexación y consultas.
    Mantiene compatibilidad con la API original.
    """
    
    def __init__(self, storage_path: str = "data/rag_storage"):
        import os
        os.makedirs(storage_path, exist_ok=True)
        
        self.storage_path = storage_path
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Inicializar servicios
        self.collection_manager = CollectionManager(storage_path)
        self.indexing = IndexingService(self.collection_manager, self.model)
        self.query = QueryService(self.collection_manager, self.model)
    
    # Métodos de compatibilidad con la API original
    def _get_collection(self, agent_id):
        """Compatibilidad con método original"""
        return self.collection_manager.get_collection(agent_id)
    
    def index_document(self, agent_id, content, metadata):
        """Compatibilidad con método original"""
        return self.indexing.index_document(agent_id, content, metadata)
    
    def rag_query(self, agent_id, query_text, top_k=5, similarity_threshold=0.75):
        """Compatibilidad con método original"""
        return self.query.rag_query(agent_id, query_text, top_k, similarity_threshold)
    
    def index_conversation_turn(self, agent_id, user_msg, assistant_msg, metadata=None):
        """Compatibilidad con método original"""
        return self.indexing.index_conversation_turn(agent_id, user_msg, assistant_msg, metadata)
    
    def process_and_index(self, agent_id, file_path):
        """Compatibilidad con método original"""
        return self.indexing.process_and_index_file(agent_id, file_path)
    
    def delete_namespace(self, agent_id):
        """Compatibilidad con método original"""
        self.collection_manager.delete_collection(agent_id)


# Exportar clases principales
__all__ = [
    'RAGEngine',
    'CollectionManager',
    'IndexingService',
    'QueryService',
    'validate_agent_id',
    'sanitize_query',
    'generate_document_id'
]

# Exportar parsers
from .parsers.markitdown_parser import MarkItDownParser
from .parsers.registry import parser_registry, register_parser

__all__ = [
    'RAGEngine',
    'CollectionManager',
    'IndexingService',
    'QueryService',
    'MarkItDownParser',
    'parser_registry',
    'register_parser',
    'validate_agent_id',
    'sanitize_query',
    'generate_document_id'
]
