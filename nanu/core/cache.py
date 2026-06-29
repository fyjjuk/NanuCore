"""Sistema de caché en disco para respuestas del LLM con invalidación selectiva."""
import hashlib
import json
import os
import time
import fnmatch
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from nanu.core.logging import get_logger

logger = get_logger(__name__)

class DiskCache:
    """Caché basada en archivos JSON con expiración por TTL e invalidación selectiva."""
    
    def __init__(self, cache_dir: str = "nanu/data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # Directorio para metadatos
        self.meta_dir = self.cache_dir / ".meta"
        self.meta_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_path(self, key: str) -> Path:
        """Retorna la ruta del archivo de caché para una clave."""
        sub = key[:2]
        path = self.cache_dir / sub / f"{key}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    
    def _get_meta_path(self, key: str) -> Path:
        """Retorna la ruta del archivo de metadatos."""
        return self.meta_dir / f"{key}.meta"
    
    def _generate_key(self, agent_id: str, route_id: str, prompt: str, system_prompt: str = "") -> str:
        """Genera una clave única a partir de los parámetros de la consulta."""
        content = f"{agent_id}|{route_id}|{prompt}|{system_prompt}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _save_metadata(self, key: str, agent_id: str, route_id: str) -> None:
        """Guarda metadatos para permitir invalidación selectiva."""
        meta_path = self._get_meta_path(key)
        try:
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'key': key,
                    'agent_id': agent_id,
                    'route_id': route_id,
                    'created_at': time.time()
                }, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando metadatos: {e}")
    
    def _get_metadata(self, key: str) -> Optional[Dict]:
        """Recupera metadatos de una clave."""
        meta_path = self._get_meta_path(key)
        if not meta_path.exists():
            return None
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def get(self, agent_id: str, route_id: str, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Recupera una respuesta cachead si existe y no ha expirado."""
        key = self._generate_key(agent_id, route_id, prompt, system_prompt)
        path = self._get_path(key)
        if not path.exists():
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'expires_at' in data and data['expires_at'] < time.time():
                self._delete_entry(key)
                logger.debug(f"Cache expirado: {key[:16]}...")
                return None
            return data.get('response')
        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.error(f"Error leyendo caché {key[:16]}...: {e}")
            return None
    
    def set(self, agent_id: str, route_id: str, prompt: str, response: str, 
            system_prompt: str = "", ttl: int = 3600) -> None:
        """Almacena una respuesta en caché con TTL en segundos."""
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
            self._save_metadata(key, agent_id, route_id)
            logger.debug(f"Cache guardado: {key[:16]}... (TTL: {ttl}s)")
        except OSError as e:
            logger.error(f"Error escribiendo caché {key[:16]}...: {e}")
    
    def _delete_entry(self, key: str) -> None:
        """Elimina una entrada de caché y sus metadatos."""
        path = self._get_path(key)
        meta_path = self._get_meta_path(key)
        try:
            if path.exists():
                path.unlink()
            if meta_path.exists():
                meta_path.unlink()
        except Exception as e:
            logger.error(f"Error eliminando entrada {key[:16]}...: {e}")
    
    def _scan_metadata(self, agent_id: Optional[str] = None, route_id: Optional[str] = None) -> List[str]:
        """Escanea metadatos y retorna claves que coinciden con los filtros."""
        keys = []
        for meta_file in self.meta_dir.glob("*.meta"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                if agent_id and meta.get('agent_id') != agent_id:
                    continue
                if route_id and meta.get('route_id') != route_id:
                    continue
                keys.append(meta.get('key'))
            except Exception:
                continue
        return keys
    
    def invalidate(self, agent_id: Optional[str] = None, route_id: Optional[str] = None,
                   pattern: Optional[str] = None) -> int:
        """
        Invalida entradas de caché.
        
        Args:
            agent_id: Filtrar por agente (opcional)
            route_id: Filtrar por ruta (opcional)
            pattern: Patrón de agente (ej. "spotify_*") (opcional)
        
        Returns:
            Número de entradas eliminadas
        """
        if agent_id is None and route_id is None and pattern is None:
            # Borrar todo el caché
            try:
                shutil.rmtree(self.cache_dir, ignore_errors=True)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                self.meta_dir.mkdir(parents=True, exist_ok=True)
                logger.info("Caché invalidado completamente")
                return 0  # No podemos contar fácilmente
            except Exception as e:
                logger.error(f"Error invalidando caché: {e}")
                return 0
        
        # Si hay patrón, expandirlo a agent_ids
        agent_ids = []
        if pattern:
            # Buscar todos los metadatos y filtrar por patrón
            meta_files = list(self.meta_dir.glob("*.meta"))
            for meta_file in meta_files:
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    if fnmatch.fnmatch(meta.get('agent_id', ''), pattern):
                        if meta.get('agent_id') not in agent_ids:
                            agent_ids.append(meta.get('agent_id'))
                except Exception:
                    continue
            if agent_ids:
                # Invalidar por cada agente encontrado
                total = 0
                for aid in agent_ids:
                    total += self.invalidate(agent_id=aid, route_id=route_id)
                return total
        
        # Invalidar por agente y/o ruta
        keys_to_delete = self._scan_metadata(agent_id, route_id)
        for key in keys_to_delete:
            self._delete_entry(key)
        
        count = len(keys_to_delete)
        if count > 0:
            logger.info(f"Cache invalidado: {count} entradas (agente={agent_id}, ruta={route_id})")
        else:
            logger.debug(f"No se encontraron entradas para invalidar (agente={agent_id}, ruta={route_id})")
        return count
    
    def stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del caché."""
        meta_files = list(self.meta_dir.glob("*.meta"))
        total_entries = len(meta_files)
        
        agent_counts = {}
        route_counts = {}
        
        for meta_file in meta_files:
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                agent = meta.get('agent_id', 'unknown')
                route = meta.get('route_id', 'unknown')
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
                route_counts[route] = route_counts.get(route, 0) + 1
            except Exception:
                continue
        
        # Calcular tamaño del caché
        total_size = 0
        for cache_file in self.cache_dir.glob("**/*.json"):
            total_size += cache_file.stat().st_size
        
        return {
            'total_entries': total_entries,
            'total_size_mb': total_size / (1024 * 1024),
            'agents': agent_counts,
            'routes': route_counts
        }
    
    def clear_expired(self) -> int:
        """Limpia entradas expiradas manualmente."""
        count = 0
        for meta_file in self.meta_dir.glob("*.meta"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                key = meta.get('key')
                if key:
                    path = self._get_path(key)
                    if path.exists():
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        if 'expires_at' in data and data['expires_at'] < time.time():
                            self._delete_entry(key)
                            count += 1
            except Exception:
                continue
        if count > 0:
            logger.info(f"Limpiadas {count} entradas expiradas")
        return count
