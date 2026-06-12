"""Plugin: Repomix Remote"""
import subprocess
import sys
import os
from core.plugin.interface import UtilityPlugin

class RepomixRemotePlugin(UtilityPlugin):
    @property
    def name(self) -> str:
        return "Repomix Remote"
    
    @property
    def description(self) -> str:
        return "Empaqueta repositorio remoto (GitHub)"
    
    @property
    def category(self) -> str:
        return "repomix"
    
    def run(self) -> None:
        script = os.path.join("scripts", "cli.py")
        subprocess.run([sys.executable, script, "repomix-remote"])
