"""
Consulta y búsqueda semántica para RAG
"""
from typing import Dict, Any, List
from core.logger import logger
from .utils import sanitize_query, validate_agent_id
from .collection import CollectionManager


class QueryService:
    """Servicio para consultas RAG (búsqueda semántica)."""
    
    def __init__(self, collection_manager: CollectionManager, embedding_model):
        self.collection_manager = collection_manager
        self.model = embedding_model
    
    def rag_query(self, agent_id: str, query_text: str, 
                  top_k: int = 5, similarity_threshold: float = 0.75) -> Dict[str, Any]:
        """
        Realiza una consulta RAG con filtro de similitud.
        
        Args:
            agent_id: Identificador del agente
            query_text: Texto de la consulta
            top_k: Número máximo de resultados
            similarity_threshold: Umbral de similitud (0-1)
            
        Returns:
            Dict con documentos, distancias y metadatos
        """
        # Validación inicial
        if not validate_agent_id(agent_id):
            return {"documents": [[]], "distances": [[]], "metadatas": [[]]}
        
        # Sanitizar query
        query_text = sanitize_query(query_text)
        if not query_text:
            logger.error("RAG_QUERY: Query vacío después de sanitización")
            return {"documents": [[]], "distances": [[]], "metadatas": [[]]}
        
        collection = self.collection_manager.get_collection(agent_id)
        if collection is None:
            return {"documents": [[]], "distances": [[]], "metadatas": [[]]}
        
        query_embedding = self.model.encode(query_text).tolist()
        
        # Pedir más resultados para filtrar después
        results = collection.query(
            query_embeddings=[query_embedding], 
            n_results=top_k * 3
        )
        
        # Filtrar por similitud
        if results and results.get('distances') and results['distances'][0]:
            filtered_docs = []
            filtered_metadatas = []
            filtered_distances = []
            
            for i, dist in enumerate(results['distances'][0]):
                # Convertir distancia a similitud
                similarity = 1 - dist if dist <= 1 else 0
                if similarity >= similarity_threshold:
                    filtered_docs.append(results['documents'][0][i])
                    filtered_distances.append(dist)
                    if results.get('metadatas') and results['metadatas'][0]:
                        filtered_metadatas.append(results['metadatas'][0][i])
            
            # Actualizar resultados
            results['documents'][0] = filtered_docs[:top_k]
            results['distances'][0] = filtered_distances[:top_k]
            if filtered_metadatas:
                results['metadatas'][0] = filtered_metadatas[:top_k]
        
        logger.info(f"RAG_QUERY: {agent_id} - {len(results['documents'][0])} resultados (threshold={similarity_threshold})")
        return results
