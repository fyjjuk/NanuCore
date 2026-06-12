"""Plugin: Backup CLI"""
import subprocess
import sys
import os
from core.plugin.interface import UtilityPlugin

class BackupCLIPlugin(UtilityPlugin):
    @property
    def name(self) -> str:
        return "Backup CLI"
    
    @property
    def description(self) -> str:
        return "Crea una copia de seguridad del proyecto"
    
    @property
    def category(self) -> str:
        return "user"
    
    def run(self) -> None:
        script = os.path.join("scripts", "user", "backup_cli.py")
        subprocess.run([sys.executable, script])
