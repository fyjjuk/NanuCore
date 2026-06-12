"""
Utilidades para RAG (validación, sanitización)
"""
import re
import logging

logger = logging.getLogger(__name__)


def validate_agent_id(agent_id: str) -> bool:
    """
    Valida que el agent_id sea seguro para usar como nombre de colección.
    
    Args:
        agent_id: Identificador del agente
        
    Returns:
        bool: True si es válido, False en caso contrario
    """
    if not agent_id or not isinstance(agent_id, str):
        logger.error(f"RAG: agent_id inválido: {agent_id}")
        return False
    
    # Solo caracteres alfanuméricos, guiones y guiones bajos
    if not re.match(r'^[a-zA-Z0-9_-]+$', agent_id):
        logger.error(f"RAG: agent_id contiene caracteres no permitidos: {agent_id}")
        return False
    
    return True


def sanitize_query(query_text: str, max_length: int = 1000) -> str:
    """
    Sanitiza una query para búsqueda RAG.
    
    Args:
        query_text: Texto de la query
        max_length: Longitud máxima permitida
        
    Returns:
        str: Query sanitizada, o cadena vacía si es inválida
    """
    if query_text is None or not isinstance(query_text, str):
        logger.error(f"RAG_QUERY: Input inválido (type={type(query_text)})")
        return ""
    
    query_text = query_text.strip()
    
    if len(query_text) > max_length:
        logger.warning(f"RAG_QUERY: Query muy largo ({len(query_text)} chars), truncando a {max_length}")
        query_text = query_text[:max_length]
    
    return query_text


def generate_document_id(agent_id: str, content: str, timestamp: str) -> str:
    """
    Genera un ID único para un documento.
    
    Args:
        agent_id: Identificador del agente
        content: Contenido del documento
        timestamp: Timestamp del documento
        
    Returns:
        str: Hash MD5 del contenido
    """
    import hashlib
    return hashlib.md5(f"{agent_id}{content}{timestamp}".encode()).hexdigest()
