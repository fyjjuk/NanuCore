"""Workspace sandbox para restringir operaciones de archivo."""
import os
from pathlib import Path
from typing import List, Optional, Union

class WorkspaceSandbox:
    """Aísla todas las operaciones de archivo a un directorio raíz."""
    
    def __init__(self, workspace_root: str):
        self.root = Path(workspace_root).resolve()
        self.real_root = self.root.resolve()  # Resolver enlaces simbólicos
        self.root.mkdir(parents=True, exist_ok=True)
    
    def resolve_path(self, user_path: str) -> Path:
        """
        Resuelve una ruta relativa al workspace, asegurando que no escape.
        Previene ataques con enlaces simbólicos y secuencias de traversal.
        """
        # Normalizar y resolver todos los enlaces simbólicos
        requested = (self.root / user_path).resolve()
        
        # Verificar que la ruta solicitada esté dentro del workspace real
        try:
            # Comparar con el root real (resuelto) para evitar enlaces simbólicos
            requested.relative_to(self.real_root)
        except ValueError:
            raise PermissionError(
                f"Acceso fuera del workspace: '{user_path}' → '{requested}' "
                f"(root: {self.real_root})"
            )
        
        # Verificación adicional: asegurar que no hay .. en el path original
        # (aunque resolve() ya maneja esto, es una capa extra)
        if '..' in user_path.split('/'):
            # Pero resolve() ya lo maneja; esta verificación es redundante
            pass
        
        return requested
    
    def safe_open(self, path: str, mode: str = 'r', *args, **kwargs):
        """Abre un archivo dentro del workspace."""
        full = self.resolve_path(path)
        return open(full, mode, *args, **kwargs)
    
    def safe_listdir(self, path: str = ".") -> List[str]:
        """Lista el contenido de un directorio dentro del workspace."""
        full = self.resolve_path(path)
        return os.listdir(full)
    
    def safe_exists(self, path: str) -> bool:
        """Verifica existencia dentro del workspace."""
        try:
            full = self.resolve_path(path)
            return full.exists()
        except PermissionError:
            return False
    
    def safe_mkdir(self, path: str, exist_ok: bool = True) -> None:
        """Crea un directorio dentro del workspace."""
        full = self.resolve_path(path)
        full.mkdir(parents=True, exist_ok=exist_ok)
    
    def safe_rm(self, path: str, recursive: bool = False) -> None:
        """Elimina un archivo o directorio dentro del workspace."""
        full = self.resolve_path(path)
        if full.is_dir() and recursive:
            import shutil
            shutil.rmtree(full)
        else:
            full.unlink()
    
    def safe_write_text(self, path: str, content: str) -> None:
        """Escribe texto a un archivo dentro del workspace."""
        with self.safe_open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def safe_read_text(self, path: str) -> str:
        """Lee texto de un archivo dentro del workspace."""
        with self.safe_open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def get_real_root(self) -> Path:
        """Retorna el root real (resuelto) del workspace."""
        return self.real_root
