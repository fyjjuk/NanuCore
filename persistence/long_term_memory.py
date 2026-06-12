"""Memoria a largo plazo usando RAG para búsqueda semántica."""
import json
import os
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from core.logger import logger

class LongTermMemory:
    """
    Memoria a largo plazo que persiste conversaciones y permite búsqueda semántica.
    Integra con RAGEngine para recuperación inteligente.
    """
    
    def __init__(self, agent_id: str, rag_engine=None, storage_dir: str = "data/long_term_memory"):
        self.agent_id = agent_id
        self.rag_engine = rag_engine
        self.storage_dir = Path(storage_dir) / agent_id
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.conversations_file = self.storage_dir / "conversations.json"
        self._load_conversations()
    
    def _load_conversations(self):
        """Carga conversaciones desde disco."""
        if self.conversations_file.exists():
            try:
                with open(self.conversations_file, 'r', encoding='utf-8') as f:
                    self.conversations = json.load(f)
            except Exception as e:
                logger.error(f"Error cargando memoria larga plazo: {e}")
                self.conversations = []
        else:
            self.conversations = []
    
    def _save_conversations(self):
        """Guarda conversaciones en disco."""
        try:
            with open(self.conversations_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error guardando memoria larga plazo: {e}")
    
    def add_interaction(self, user_input: str, assistant_output: str, metadata: Dict[str, Any] = None):
        """
        Añade una interacción a la memoria a largo plazo.
        """
        interaction = {
            "id": hashlib.md5(f"{self.agent_id}{datetime.now().isoformat()}{user_input}".encode()).hexdigest()[:12],
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "assistant_output": assistant_output,
            "metadata": metadata or {}
        }
        
        self.conversations.append(interaction)
        
        # Mantener solo últimas 1000 conversaciones
        if len(self.conversations) > 1000:
            self.conversations = self.conversations[-1000:]
        
        self._save_conversations()
        
        # Indexar en RAG si está disponible
        if self.rag_engine:
            try:
                content = f"Usuario: {user_input}\nAsistente: {assistant_output}"
                self.rag_engine.index_document(
                    self.agent_id,
                    content,
                    {"type": "conversation", "timestamp": interaction["timestamp"], "id": interaction["id"]}
                )
            except Exception as e:
                logger.warning(f"Error indexando en RAG: {e}")
        
        logger.info(f"Memoria larga plazo: añadida interacción {interaction['id']} para agente {self.agent_id}")
    
    def recall_similar(self, query: str, top_k: int = 3, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Recupera interacciones similares usando búsqueda semántica.
        """
        results = []
        
        # Primero intentar con RAG
        if self.rag_engine:
            try:
                rag_results = self.rag_engine.rag_query(
                    self.agent_id, 
                    query, 
                    top_k=top_k,
                    similarity_threshold=similarity_threshold
                )
                
                if rag_results and rag_results.get('documents') and rag_results['documents'][0]:
                    for i, doc in enumerate(rag_results['documents'][0][:top_k]):
                        # Parsear documento para extraer usuario/asistente
                        lines = doc.split('\n')
                        user_msg = ""
                        assistant_msg = ""
                        for line in lines:
                            if line.startswith("Usuario:"):
                                user_msg = line.replace("Usuario:", "").strip()
                            elif line.startswith("Asistente:"):
                                assistant_msg = line.replace("Asistente:", "").strip()
                        
                        results.append({
                            "user_input": user_msg,
                            "assistant_output": assistant_msg,
                            "similarity": 1 - rag_results.get('distances', [[0]])[0][i] if rag_results.get('distances') else 0.8,
                            "source": "rag"
                        })
                    
                    if results:
                        logger.info(f"Memoria larga plazo: {len(results)} resultados de RAG para query '{query[:50]}...'")
                        return results
            except Exception as e:
                logger.warning(f"Error en búsqueda RAG: {e}")
        
        # Fallback: búsqueda por keywords en conversaciones locales
        query_lower = query.lower()
        keywords = set(query_lower.split())
        
        for conv in reversed(self.conversations):  # Más recientes primero
            user_lower = conv["user_input"].lower()
            # Calcular solapamiento de keywords
            matches = sum(1 for kw in keywords if kw in user_lower)
            if matches > 0:
                similarity = matches / len(keywords) if keywords else 0
                if similarity >= similarity_threshold:
                    results.append({
                        "user_input": conv["user_input"],
                        "assistant_output": conv["assistant_output"],
                        "timestamp": conv["timestamp"],
                        "similarity": similarity,
                        "source": "local"
                    })
        
        # Ordenar por similitud y limitar
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:top_k]
        
        logger.info(f"Memoria larga plazo: {len(results)} resultados locales para query '{query[:50]}...'")
        return results
    
    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene las interacciones más recientes."""
        return self.conversations[-limit:]
    
    def clear(self):
        """Limpia toda la memoria a largo plazo."""
        self.conversations = []
        self._save_conversations()
        if self.rag_engine:
            try:
                self.rag_engine.delete_namespace(self.agent_id)
            except:
                pass
        logger.info(f"Memoria larga plazo limpiada para agente {self.agent_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas de la memoria."""
        return {
            "total_interactions": len(self.conversations),
            "oldest": self.conversations[0]["timestamp"] if self.conversations else None,
            "newest": self.conversations[-1]["timestamp"] if self.conversations else None,
            "rag_available": self.rag_engine is not None
        }
