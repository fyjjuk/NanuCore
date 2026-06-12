import json
import os
from datetime import datetime
from pathlib import Path
from core.logger import logger
from core.tracing import get_request_id

class ApprovalAudit:
    """Registro de aprobaciones/rechazos del Gatekeeper."""
    
    def __init__(self, audit_file: str = "logs/approvals.log"):
        self.audit_file = Path(audit_file)
        # Crear directorio si no existe
        self.audit_file.parent.mkdir(exist_ok=True)
    
    def log_approval(self, route_id: str, approved: bool, reason: str = "", metadata: dict = None) -> None:
        """Registra una decisión de aprobación."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "request_id": get_request_id() or "unknown",
            "route_id": route_id,
            "approved": approved,
            "reason": reason,
            "metadata": metadata or {}
        }
        
        try:
            with open(self.audit_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            logger.info(f"Audit: {route_id} - {'APROBADO' if approved else 'RECHAZADO'}")
        except Exception as e:
            logger.error(f"Error escribiendo audit log: {e}")
    
    def get_recent(self, limit: int = 50) -> list:
        """Obtiene las últimas entradas del audit log."""
        if not self.audit_file.exists():
            return []
        
        entries = []
        with open(self.audit_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entries.append(json.loads(line.strip()))
                except:
                    continue
        return entries[-limit:]

# Instancia global
audit = ApprovalAudit()
