"""Plugin: Export Project"""
import subprocess
import sys
import os
from core.plugin.interface import UtilityPlugin

class ExportProjectPlugin(UtilityPlugin):
    @property
    def name(self) -> str:
        return "Export Project"
    
    @property
    def description(self) -> str:
        return "Exporta el proyecto con estructura y contenido"
    
    @property
    def category(self) -> str:
        return "user"
    
    def run(self) -> None:
        script = os.path.join("scripts", "user", "export_project_v2.py")
        subprocess.run([sys.executable, script])
