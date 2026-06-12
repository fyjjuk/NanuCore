"""Plugin: Project Info"""
import subprocess
import sys
import os
from core.plugin.interface import UtilityPlugin

class ProjectInfoPlugin(UtilityPlugin):
    @property
    def name(self) -> str:
        return "Project Info"
    
    @property
    def description(self) -> str:
        return "Muestra información detallada del proyecto"
    
    @property
    def category(self) -> str:
        return "diagnostic"
    
    def run(self) -> None:
        script = os.path.join("scripts", "diagnostic", "project_info.py")
        subprocess.run([sys.executable, script])
