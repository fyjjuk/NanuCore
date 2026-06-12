"""Plugin: Repomix Basic"""
import subprocess
import sys
import os
from core.plugin.interface import UtilityPlugin

class RepomixBasicPlugin(UtilityPlugin):
    @property
    def name(self) -> str:
        return "Repomix Basic"
    
    @property
    def description(self) -> str:
        return "Exporta en formato XML básico"
    
    @property
    def category(self) -> str:
        return "repomix"
    
    def run(self) -> None:
        script = os.path.join("scripts", "cli.py")
        subprocess.run([sys.executable, script, "repomix-xml"])
