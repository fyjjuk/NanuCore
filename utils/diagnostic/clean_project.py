"""Plugin: Clean Project"""
import subprocess
import sys
import os
from core.plugin.interface import UtilityPlugin

class CleanProjectPlugin(UtilityPlugin):
    @property
    def name(self) -> str:
        return "Clean Project"
    
    @property
    def description(self) -> str:
        return "Limpia archivos temporales y caché"
    
    @property
    def category(self) -> str:
        return "diagnostic"
    
    def run(self) -> None:
        script = os.path.join("scripts", "diagnostic", "clean_project.py")
        subprocess.run([sys.executable, script])
