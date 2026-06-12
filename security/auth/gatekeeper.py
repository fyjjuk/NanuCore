import sys
import select
import logging
from typing import Optional
from security.auth.audit import ApprovalAudit

logger = logging.getLogger("ferdonan.core.gatekeeper")

class Gatekeeper:
    def __init__(self, default_timeout: int = 60, force_all: bool = False, ui_renderer=None):
        self.default_timeout = default_timeout
        self.force_all = force_all
        self._session_cache = {}
        self._session_id = id(self)
        self.ui = ui_renderer  # Inyección de UI (opcional)
        self.audit = ApprovalAudit()

    def verify(self, route_id: str, route_config: dict, request_id: str) -> bool:
        # Verificar caché de sesión
        if route_id in self._session_cache:
            cached_decision = self._session_cache[route_id]
            logger.info(f"Gatekeeper usando decisión en caché para ruta '{route_id}': {'aprobada' if cached_decision else 'rechazada'}")
            
            if self.ui:
                msg = self.ui.render_info(f"Usando decisión previa para '{route_id}' (aprobada: {cached_decision})")
                print(f"\033[90m{msg}\033[0m")
            else:
                print(f"\033[90m[GATEKEEPER] Usando decisión previa para '{route_id}' (aprobada: {cached_decision})\033[0m")
            return cached_decision

        # Determinar si se requiere Gatekeeper
        gatekeeper_required = route_config.get("gatekeeper_required", False)
        
        if not gatekeeper_required and not self.force_all:
            self._session_cache[route_id] = True
            return True

        # Solicitar aprobación humana
        if self.ui:
            badge = self.ui.render_badge("GATEKEEPER", "gatekeeper")
            msg = self.ui.render_warning(f"La ruta '{route_id}' requiere aprobación humana.")
            print(f"\n{badge} {msg}")
            print(f"[REQUEST ID: {request_id}] {self.ui.render_prompt('¿Permitir ejecución? (Y/N): ')}", end="", flush=True)
        else:
            print(f"\n[GATEKEEPER] ATENCIÓN: La ruta '{route_id}' requiere aprobación humana.")
            print(f"[REQUEST ID: {request_id}] ¿Desea permitir la ejecución? (Y/N): ", end="", flush=True)

        # Implementación de timeout compatible con POSIX
        rlist, _, _ = select.select([sys.stdin], [], [], self.default_timeout)
        
        if rlist:
            user_input = sys.stdin.readline().strip().upper()
            if user_input == 'Y':
                self.audit.log_approval(route_id, True, "Aprobado por usuario", {"input": "Y"})
                self._session_cache[route_id] = True
                if self.ui:
                    success_msg = self.ui.render_success("Acción confirmada por el usuario.")
                    print(f"\n{success_msg}")
                else:
                    print("\n[GATEKEEPER] Acción confirmada por el usuario.")
                return True
            else:
                self.audit.log_approval(route_id, False, "Rechazado por usuario", {"input": user_input})
                self._session_cache[route_id] = False
                if self.ui:
                    error_msg = self.ui.render_error("Acción rechazada por el usuario.")
                    print(f"\n{error_msg}")
                else:
                    print("\n[GATEKEEPER] Acción rechazada por el usuario.")
                return False
        else:
            self.audit.log_approval(route_id, False, f"Timeout después de {self.default_timeout}s")
            self._session_cache[route_id] = False
            if self.ui:
                error_msg = self.ui.render_error(f"Tiempo de espera agotado ({self.default_timeout}s). Acción rechazada por defecto (Fail-Closed).")
                print(f"\n{error_msg}")
            else:
                print(f"\n[GATEKEEPER] Tiempo de espera agotado ({self.default_timeout}s). Acción rechazada por defecto (Fail-Closed).")
            return False
