"""
Manejo de colecciones ChromaDB para RAG
"""
import chromadb
from chromadb.utils import embedding_functions
from core.logger import logger
from .utils import validate_agent_id


class CollectionManager:
    """Gestiona la creación y acceso a colecciones ChromaDB."""
    
    def __init__(self, storage_path: str = "data/rag_storage"):
        self.storage_path = storage_path
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name='all-MiniLM-L6-v2'
        )
        self.client = chromadb.PersistentClient(path=storage_path)
        self.collection_cache = {}
    
    def get_collection(self, agent_id: str):
        """
        Obtiene o crea una colección para un agente.
        
        Args:
            agent_id: Identificador del agente
            
        Returns:
            ChromaDB collection o None si error
        """
        if not validate_agent_id(agent_id):
            return None
        
        if agent_id in self.collection_cache:
            return self.collection_cache[agent_id]
        
        name = f"agent_{agent_id}_knowledge"
        collection = self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_fn
        )
        self.collection_cache[agent_id] = collection
        return collection
    
    def delete_collection(self, agent_id: str):
        """
        Elimina la colección de un agente.
        
        Args:
            agent_id: Identificador del agente
        """
        if not validate_agent_id(agent_id):
            return
        
        try:
            self.client.delete_collection(f"agent_{agent_id}_knowledge")
            if agent_id in self.collection_cache:
                del self.collection_cache[agent_id]
            logger.info(f"RAG_NAMESPACE_DELETED: {agent_id}")
        except Exception as e:
            logger.error(f"Error eliminando colección para {agent_id}: {e}")
