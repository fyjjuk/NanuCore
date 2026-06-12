"""Gatekeeper mejorado con aprobación humana, caché por sesión y auditoría."""
import asyncio
import sys
import time
from typing import Dict, Any, Optional
from pathlib import Path

# Importar auditoría (adaptada del módulo original)
try:
    from security.auth.audit import ApprovalAudit
except ImportError:
    # Fallback si no existe el módulo original
    class ApprovalAudit:
        def log_approval(self, route_id, approved, reason="", metadata=None):
            print(f"[AUDIT] {route_id} {'APROBADO' if approved else 'REICHADO'} - {reason}")

class Gatekeeper:
    def __init__(self, default_timeout: int = 60, force_all: bool = False, 
                 session_ttl: int = 300, ui_renderer=None):
        self.default_timeout = default_timeout
        self.force_all = force_all
        self.session_ttl = session_ttl  # segundos para expirar caché de sesión
        self._session_cache: Dict[str, Dict] = {}  # {route_id: {"approved": bool, "timestamp": float}}
        self.ui = ui_renderer
        self.audit = ApprovalAudit()
    
    def _get_cache_key(self, route_id: str, session_id: str = None) -> str:
        """Clave de caché: ruta + sesión (si se proporciona)."""
        if session_id:
            return f"{route_id}:{session_id}"
        return route_id
    
    def _is_cached(self, route_id: str, session_id: str = None) -> Optional[bool]:
        """Retorna decisión cachead si no ha expirado."""
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
        Verifica si la ruta está aprobada.
        - Si force_all está activado, siempre requiere aprobación (ignora gatekeeper_required).
        - Si no, solo si gatekeeper_required=True.
        - Si está en caché de sesión, usa esa decisión.
        - Si no, pregunta al usuario (asíncrono) y guarda en caché.
        """
        # Determinar si se requiere aprobación
        gatekeeper_required = route_config.get("gatekeeper_required", False)
        if not gatekeeper_required and not self.force_all:
            # No requiere aprobación, permitir y no cachear (ya que es default)
            return True
        
        # Verificar caché
        cached = self._is_cached(route_id, session_id)
        if cached is not None:
            self.audit.log_approval(route_id, cached, "Usando decisión en caché", 
                                    {"session_id": session_id, "cached": True})
            return cached
        
        # Obtener timeout específico de la ruta o usar el global
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
        
        # Esperar entrada del usuario en un hilo separado para no bloquear el event loop
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
            self.audit.log_approval(route_id, True, "Aprobado por usuario", 
                                    {"request_id": request_id, "session_id": session_id})
            if self.ui:
                print(f"\n{self.ui.render_success('Acción confirmada por el usuario.')}")
            else:
                print("\n[GATEKEEPER] Acción confirmada por el usuario.")
        else:
            approved = False
            reason = "Rechazado por usuario" if user_input is not None else f"Timeout después de {timeout}s"
            self.audit.log_approval(route_id, False, reason, 
                                    {"request_id": request_id, "session_id": session_id})
            if self.ui:
                print(f"\n{self.ui.render_error(f'Acción rechazada: {reason}')}")
            else:
                print(f"\n[GATEKEEPER] Acción rechazada: {reason}")
        
        # Cachear la decisión (solo para esta sesión)
        self._cache_decision(route_id, approved, session_id)
        return approved

# Instancia global (opcional, se puede crear en orchestrator)
gatekeeper = None
