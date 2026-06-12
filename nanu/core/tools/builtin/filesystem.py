"""Herramienta de sistema de archivos con sandbox."""
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from nanu.core.interfaces import Tool
from nanu.core.security.sandbox import WorkspaceSandbox

class FilesystemTool(Tool):
    name = "filesystem"
    description = "Operaciones de archivo dentro del workspace: read, write, list, mkdir, rm, exists"
    enabled = True

    async def execute(self, args: Dict[str, Any], workspace: Optional[WorkspaceSandbox] = None) -> str:
        if workspace is None:
            return "Error: no se proporcionó sandbox"
        
        action = args.get("action", "")
        path = args.get("path", "")
        content = args.get("content", "")
        
        if not path:
            return "Error: se requiere 'path'"
        
        try:
            if action == "read":
                return workspace.safe_read_text(path)
            elif action == "write":
                workspace.safe_write_text(path, content)
                return f"✅ Escrito en {path}"
            elif action == "list":
                items = workspace.safe_listdir(path)
                return "\n".join(items) if items else "(vacío)"
            elif action == "mkdir":
                workspace.safe_mkdir(path)
                return f"✅ Directorio creado: {path}"
            elif action == "rm":
                recursive = args.get("recursive", False)
                workspace.safe_rm(path, recursive=recursive)
                return f"✅ Eliminado: {path}"
            elif action == "exists":
                return "true" if workspace.safe_exists(path) else "false"
            else:
                return f"Acción desconocida: {action}. Opciones: read, write, list, mkdir, rm, exists"
        except PermissionError as e:
            return f"❌ Acceso denegado: {e}"
        except Exception as e:
            return f"❌ Error: {e}"

__all__ = ["FilesystemTool"]
