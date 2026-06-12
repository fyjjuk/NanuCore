"""Sistema de caché en disco para respuestas del LLM."""
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any

class DiskCache:
    """Caché simple basada en archivos JSON con expiración por TTL."""
    
    def __init__(self, cache_dir: str = "nanu/data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_path(self, key: str) -> Path:
        """Retorna la ruta del archivo de caché para una clave."""
        # Usar subdirectorios para evitar muchos archivos en una carpeta
        sub = key[:2]
        path = self.cache_dir / sub / f"{key}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    
    def _generate_key(self, agent_id: str, route_id: str, prompt: str, system_prompt: str = "") -> str:
        """Genera una clave única a partir de los parámetros de la consulta."""
        content = f"{agent_id}|{route_id}|{prompt}|{system_prompt}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, agent_id: str, route_id: str, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Recupera una respuesta cachead si existe y no ha expirado."""
        key = self._generate_key(agent_id, route_id, prompt, system_prompt)
        path = self._get_path(key)
        if not path.exists():
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Verificar expiración (TTL en segundos)
            if 'expires_at' in data and data['expires_at'] < time.time():
                path.unlink()  # Eliminar expirado
                return None
            return data.get('response')
        except (json.JSONDecodeError, KeyError, OSError):
            return None
    
    def set(self, agent_id: str, route_id: str, prompt: str, response: str, 
            system_prompt: str = "", ttl: int = 3600) -> None:
        """Almacena una respuesta en caché con TTL en segundos (por defecto 1 hora)."""
        key = self._generate_key(agent_id, route_id, prompt, system_prompt)
        path = self._get_path(key)
        data = {
            'response': response,
            'created_at': time.time(),
            'expires_at': time.time() + ttl,
            'agent_id': agent_id,
            'route_id': route_id
        }
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"Error escribiendo caché: {e}")
    
    def invalidate(self, agent_id: Optional[str] = None, route_id: Optional[str] = None) -> None:
        """Invalida entradas de caché (todas, por agente, o por ruta)."""
        if agent_id is None:
            # Borrar todo el caché
            import shutil
            shutil.rmtree(self.cache_dir, ignore_errors=True)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            return
        
        # Buscar archivos que contengan agent_id en la clave
        # Como las claves son hashes, no podemos filtrar fácilmente.
        # Una aproximación: almacenar metadatos separados o simplemente no implementar filtrado por ahora.
        # Por simplicidad, solo soportamos invalidación total.
        raise NotImplementedError("Invalidación selectiva no implementada aún")
