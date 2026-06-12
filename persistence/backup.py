import os
import shutil
import json
import datetime
import tarfile
import io
from pathlib import Path
from core.logger import logger

class BackupManager:
    def __init__(self, backup_dir="backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, name=None):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = name or f"ferdonan_backup_{timestamp}"
        backup_path = self.backup_dir / f"{backup_name}.tar.gz"
        
        # Directorios y archivos a respaldar (estructura modular completa)
        items_to_backup = [
            "agents",
            "config",
            "core",
            "models",
            "modules",
            "orchestration",
            "persistence",
            "scripts",
            "security",
            "services",
            "tests",
            "tools",
            "ui",
            "main.py",
            "requirements.txt",
            "README.md"
        ]
        
        with tarfile.open(backup_path, "w:gz") as tar:
            for item in items_to_backup:
                if os.path.exists(item):
                    tar.add(item)
            
            # Guardar metadata
            metadata = {
                "backup_name": backup_name,
                "timestamp": timestamp,
                "items": items_to_backup,
                "version": "2.0"  # versión modular
            }
            metadata_str = json.dumps(metadata, indent=2)
            tarinfo = tarfile.TarInfo(name="backup_metadata.json")
            tarinfo.size = len(metadata_str)
            tar.addfile(tarinfo, fileobj=io.BytesIO(metadata_str.encode()))
        
        logger.info(f"Backup creado: {backup_path}")
        return backup_path

    def list_backups(self):
        backups = list(self.backup_dir.glob("*.tar.gz"))
        result = []
        for b in backups:
            stat = b.stat()
            result.append({
                "name": b.name,
                "size_mb": stat.st_size / (1024 * 1024),
                "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        return result

    def restore_backup(self, backup_name):
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup {backup_name} no encontrado")
        
        # Crear directorio temporal
        temp_dir = self.backup_dir / "temp_restore"
        temp_dir.mkdir(exist_ok=True)
        
        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(temp_dir)
        
        logger.warning(f"Backup restaurado en {temp_dir}. Revisa antes de copiar.")
        return temp_dir

    def auto_backup_on_change(self, watch_paths=None):
        """Simplificado: genera backup automático antes de operaciones críticas"""
        return self.create_backup(name="auto_pre_change")
