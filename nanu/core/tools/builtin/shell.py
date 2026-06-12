"""Herramienta de shell con allowlist de comandos."""
import subprocess
import shlex
from typing import Dict, Any, Optional, List
from nanu.core.interfaces import Tool

class ShellTool(Tool):
    name = "shell"
    description = "Ejecuta comandos del sistema (restringido por allowlist)"
    enabled = False  # Deshabilitado por defecto por seguridad
    
    # Comandos permitidos (solo lectura/consulta)
    ALLOWED_COMMANDS = [
        "ls", "cat", "head", "tail", "grep", "wc", "find", "stat",
        "ps", "top", "df", "du", "free", "uptime", "whoami", "hostname"
    ]
    
    async def execute(self, args: Dict[str, Any], workspace: Optional = None) -> str:
        if not self.enabled:
            return "❌ Herramienta shell deshabilitada por seguridad"
        
        command = args.get("command", "")
        if not command:
            return "Error: se requiere 'command'"
        
        # Dividir comando y argumentos
        parts = shlex.split(command)
        if not parts:
            return "Comando vacío"
        
        cmd_name = parts[0]
        if cmd_name not in self.ALLOWED_COMMANDS:
            return f"❌ Comando no permitido: {cmd_name}. Permitidos: {', '.join(self.ALLOWED_COMMANDS)}"
        
        try:
            result = subprocess.run(
                parts, capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout.strip() or "(sin salida)"
            else:
                return f"Error ({result.returncode}): {result.stderr.strip()}"
        except subprocess.TimeoutExpired:
            return "Error: tiempo de espera agotado"
        except Exception as e:
            return f"Error: {e}"

__all__ = ["ShellTool"]
