"""Plugin: Health Check CLI"""
import subprocess
import sys
import os
from core.plugin.interface import UtilityPlugin

class HealthCheckCLIPlugin(UtilityPlugin):
    @property
    def name(self) -> str:
        return "Health Check (CLI)"
    
    @property
    def description(self) -> str:
        return "Verifica salud del sistema"
    
    @property
    def category(self) -> str:
        return "cli"
    
    def run(self) -> None:
        script = os.path.join("scripts", "cli.py")
        subprocess.run([sys.executable, script, "health"])
