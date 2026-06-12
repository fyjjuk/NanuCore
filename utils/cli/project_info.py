"""Plugin: Project Info CLI"""
import subprocess
import sys
import os
from core.plugin.interface import UtilityPlugin

class ProjectInfoCLIPlugin(UtilityPlugin):
    @property
    def name(self) -> str:
        return "Project Info (CLI)"
    
    @property
    def description(self) -> str:
        return "Información detallada del proyecto"
    
    @property
    def category(self) -> str:
        return "cli"
    
    def run(self) -> None:
        script = os.path.join("scripts", "cli.py")
        subprocess.run([sys.executable, script, "info"])
