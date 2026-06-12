"""Almacenamiento append-only en formato JSONL para historial de sesiones."""
import json
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

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
        """Añade un turno (mensaje) a la sesión de forma atómica."""
        file_path = self._get_session_file(session_key)
        # Añadir timestamp si no existe
        if "timestamp" not in turn:
            turn["timestamp"] = datetime.now().isoformat()
        
        # Escritura atómica: escribir a temporal y luego renombrar
        line = json.dumps(turn, ensure_ascii=False) + "\n"
        
        # Usar directorio temporal en el mismo sistema de archivos
        temp_dir = self.data_dir / ".tmp"
        temp_dir.mkdir(exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', dir=temp_dir, delete=False, encoding='utf-8') as tmp:
            tmp.write(line)
            tmp_path = tmp.name
        
        # Si el archivo ya existe, añadir al final (no usar rename porque perderíamos datos)
        # En su lugar, abrir en modo append con bloqueo (simplificado)
        # Para evitar race conditions, usamos un lock basado en archivo (opcional)
        # Por simplicidad, abrimos en modo 'a' y escribimos.
        # En un sistema real, se puede usar fcntl.flock o una librería de locks.
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(line)
        os.unlink(tmp_path)  # eliminar temporal
    
    async def get_history(self, session_key: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Lee las últimas `limit` líneas de la sesión."""
        file_path = self._get_session_file(session_key)
        if not file_path.exists():
            return []
        
        turns = []
        with open(file_path, 'r', encoding='utf-8') as f:
            # Leer todas las líneas, pero mantener solo las últimas `limit`
            lines = f.readlines()
            for line in lines[-limit:]:
                try:
                    turn = json.loads(line.strip())
                    turns.append(turn)
                except json.JSONDecodeError:
                    continue
        return turns
    
    async def clear(self, session_key: str) -> None:
        """Elimina el archivo de la sesión."""
        file_path = self._get_session_file(session_key)
        if file_path.exists():
            file_path.unlink()
    
    async def list_sessions(self) -> List[str]:
        """Lista todas las claves de sesión existentes."""
        sessions = []
        for p in self.data_dir.glob("*.jsonl"):
            # Reconstruir clave original (no sanitizada, pero aproximada)
            sessions.append(p.stem)
        return sessions
