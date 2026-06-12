"""Plugin: Find Duplicates"""
import subprocess
import sys
import os
from core.plugin.interface import UtilityPlugin

class FindDuplicatesPlugin(UtilityPlugin):
    @property
    def name(self) -> str:
        return "Find Duplicates"
    
    @property
    def description(self) -> str:
        return "Busca archivos duplicados en el proyecto"
    
    @property
    def category(self) -> str:
        return "diagnostic"
    
    def run(self) -> None:
        script = os.path.join("scripts", "diagnostic", "find_duplicates.py")
        subprocess.run([sys.executable, script])
