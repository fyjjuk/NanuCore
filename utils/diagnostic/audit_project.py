"""Plugin: Audit Project"""
import subprocess
import sys
import os
from core.plugin.interface import UtilityPlugin

class AuditProjectPlugin(UtilityPlugin):
    @property
    def name(self) -> str:
        return "Audit Project"
    
    @property
    def description(self) -> str:
        return "Analiza el proyecto y clasifica archivos"
    
    @property
    def category(self) -> str:
        return "diagnostic"
    
    def run(self) -> None:
        script = os.path.join("scripts", "diagnostic", "audit_project.py")
        subprocess.run([sys.executable, script])
