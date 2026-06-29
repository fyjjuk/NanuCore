"""Almacenamiento append-only en formato JSONL para historial de sesiones."""
import json
import os
import tempfile
import shutil
import fcntl
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from nanu.core.logging import get_logger

logger = get_logger(__name__)


class JSONLMemory:
    """Memoria persistente usando archivos JSONL (una línea por mensaje)."""
    
    def __init__(self, data_dir: str = "nanu/data/sessions"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_session_file(self, session_key: str) -> Path:
        """Retorna la ruta del archivo JSONL para una sesión."""
        # Sanitizar clave para usar como nombre de archivo
        safe_key = "".join(c for c in session_key if c.isalnum() or c in "._-")
        return self.data_dir / f"{safe_key}.jsonl"
    
    async def add(self, session_key: str, turn: Dict[str, Any]) -> None:
        """
        Añade un turno (mensaje) a la sesión de forma atómica con bloqueo.
        Usa fcntl.flock para evitar race conditions en escritura concurrente.
        """
        file_path = self._get_session_file(session_key)
        
        # Añadir timestamp si no existe
        if "timestamp" not in turn:
            turn["timestamp"] = datetime.now().isoformat()
        
        line = json.dumps(turn, ensure_ascii=False) + "\n"
        
        # Escribir con bloqueo exclusivo
        try:
            # Abrir en modo append con bloqueo
            with open(file_path, 'a', encoding='utf-8') as f:
                # Adquirir bloqueo exclusivo
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                f.write(line)
                f.flush()  # Forzar escritura en disco
                # Liberar bloqueo (se libera automáticamente al cerrar)
        except Exception as e:
            logger.error(f"Error escribiendo en {file_path}: {e}")
            raise
    
    async def get_history(self, session_key: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Lee las últimas `limit` líneas de la sesión."""
        file_path = self._get_session_file(session_key)
        if not file_path.exists():
            return []
        
        turns = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Adquirir bloqueo compartido para lectura
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                # Leer todas las líneas
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        turn = json.loads(line.strip())
                        turns.append(turn)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Error leyendo {file_path}: {e}")
            return []
        
        return turns
    
    async def clear(self, session_key: str) -> None:
        """Elimina el archivo de la sesión."""
        file_path = self._get_session_file(session_key)
        if file_path.exists():
            try:
                file_path.unlink()
                logger.debug(f"Sesión eliminada: {session_key}")
            except Exception as e:
                logger.error(f"Error eliminando {file_path}: {e}")
    
    async def list_sessions(self) -> List[str]:
        """Lista todas las claves de sesión existentes."""
        sessions = []
        for p in self.data_dir.glob("*.jsonl"):
            sessions.append(p.stem)
        return sessions
    
    async def get_history_all(self, session_key: str) -> List[Dict[str, Any]]:
        """Lee todo el historial de una sesión."""
        return await self.get_history(session_key, limit=999999)
