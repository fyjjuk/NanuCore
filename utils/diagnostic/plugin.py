"""Plugin: Health Check"""
import subprocess
import sys
import os
from core.plugin.interface import UtilityPlugin

class HealthCheckPlugin(UtilityPlugin):
    @property
    def name(self) -> str:
        return "Health Check"
    
    @property
    def description(self) -> str:
        return "Verifica el estado del sistema y dependencias"
    
    @property
    def category(self) -> str:
        return "diagnostic"
    
    def run(self) -> None:
        script = os.path.join("scripts", "diagnostic", "check_health.py")
        subprocess.run([sys.executable, script])
