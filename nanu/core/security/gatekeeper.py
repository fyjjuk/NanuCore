"""Gatekeeper mejorado con aprobación humana, caché por sesión y auditoría persistente."""
import asyncio
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from nanu.core.logging import get_logger

logger = get_logger(__name__)


class ApprovalAudit:
    """Auditoría persistente de decisiones del Gatekeeper en formato JSONL."""
    
    def __init__(self, log_dir: str = "nanu/data/audit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_log_file(self) -> Path:
        """Retorna la ruta del archivo de log para hoy."""
        today = datetime.now().strftime('%Y%m%d')
        return self.log_dir / f"audit_{today}.jsonl"
    
    def log_approval(self, route_id: str, approved: bool, reason: str = "", 
                     metadata: Optional[Dict] = None) -> None:
        """
        Registra una decisión de aprobación en el archivo de auditoría.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "route_id": route_id,
            "approved": approved,
            "reason": reason,
            "metadata": metadata or {},
        }
        
        log_file = self._get_log_file()
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            logger.debug(f"Auditoría registrada: {route_id} → {'APROBADO' if approved else 'RECHAZADO'}")
        except Exception as e:
            logger.error(f"Error escribiendo auditoría: {e}")
    
    def get_history(self, limit: int = 100) -> list:
        """Retorna las últimas entradas de auditoría."""
        log_file = self._get_log_file()
        if not log_file.exists():
            return []
        
        entries = []
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entries.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
            return entries[-limit:]
        except Exception as e:
            logger.error(f"Error leyendo auditoría: {e}")
            return []


class Gatekeeper:
    def __init__(self, default_timeout: int = 60, force_all: bool = False, 
                 session_ttl: int = 300, ui_renderer=None):
        self.default_timeout = default_timeout
        self.force_all = force_all
        self.session_ttl = session_ttl
        self._session_cache: Dict[str, Dict] = {}
        self.ui = ui_renderer
        self.audit = ApprovalAudit()
    
    def _get_cache_key(self, route_id: str, session_id: str = None) -> str:
        if session_id:
            return f"{route_id}:{session_id}"
        return route_id
    
    def _is_cached(self, route_id: str, session_id: str = None) -> Optional[bool]:
        key = self._get_cache_key(route_id, session_id)
        entry = self._session_cache.get(key)
        if entry and (time.time() - entry["timestamp"]) < self.session_ttl:
            return entry["approved"]
        return None
    
    def _cache_decision(self, route_id: str, approved: bool, session_id: str = None) -> None:
        key = self._get_cache_key(route_id, session_id)
        self._session_cache[key] = {"approved": approved, "timestamp": time.time()}
    
    async def verify(self, route_id: str, route_config: Dict[str, Any], 
                     request_id: str, session_id: Optional[str] = None) -> bool:
        """
        Verifica si la ruta está aprobada con auditoría persistente.
        """
        gatekeeper_required = route_config.get("gatekeeper_required", False)
        if not gatekeeper_required and not self.force_all:
            # No requiere aprobación, se permite
            self.audit.log_approval(
                route_id, True, "gatekeeper_required=false",
                {"force_all": False, "session_id": session_id}
            )
            return True
        
        # Verificar caché
        cached = self._is_cached(route_id, session_id)
        if cached is not None:
            self.audit.log_approval(
                route_id, cached, "cached",
                {"session_id": session_id, "cached": True}
            )
            return cached
        
        timeout = route_config.get("gatekeeper_timeout", self.default_timeout)
        
        # Solicitar aprobación humana
        if self.ui:
            badge = self.ui.render_badge("GATEKEEPER", "gatekeeper")
            msg = self.ui.render_warning(f"La ruta '{route_id}' requiere aprobación humana.")
            print(f"\n{badge} {msg}")
            print(f"[REQUEST ID: {request_id}] {self.ui.render_prompt('¿Permitir ejecución? (Y/N): ')}", end="", flush=True)
        else:
            print(f"\n[GATEKEEPER] ATENCIÓN: La ruta '{route_id}' requiere aprobación humana.")
            print(f"[REQUEST ID: {request_id}] ¿Permitir ejecución? (Y/N): ", end="", flush=True)
        
        try:
            loop = asyncio.get_running_loop()
            user_input = await asyncio.wait_for(
                loop.run_in_executor(None, sys.stdin.readline),
                timeout=timeout
            )
            user_input = user_input.strip().upper()
        except asyncio.TimeoutError:
            user_input = None
        
        if user_input == 'Y':
            approved = True
            reason = "Aprobado por usuario"
            if self.ui:
                print(f"\n{self.ui.render_success('Acción confirmada por el usuario.')}")
            else:
                print("\n[GATEKEEPER] Acción confirmada por el usuario.")
        else:
            approved = False
            reason = "Rechazado por usuario" if user_input is not None else f"Timeout después de {timeout}s"
            if self.ui:
                print(f"\n{self.ui.render_error(f'Acción rechazada: {reason}')}")
            else:
                print(f"\n[GATEKEEPER] Acción rechazada: {reason}")
        
        # Registrar auditoría
        self.audit.log_approval(
            route_id, approved, reason,
            {"request_id": request_id, "session_id": session_id, "timeout": timeout}
        )
        
        self._cache_decision(route_id, approved, session_id)
        return approved

# Instancia global
gatekeeper = None
