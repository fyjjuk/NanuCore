"""Plugin: Validate Routes"""
import subprocess
import sys
import os
from core.plugin.interface import UtilityPlugin

class ValidateRoutesPlugin(UtilityPlugin):
    @property
    def name(self) -> str:
        return "Validate Routes"
    
    @property
    def description(self) -> str:
        return "Valida todas las rutas YAML de los agentes"
    
    @property
    def category(self) -> str:
        return "diagnostic"
    
    def run(self) -> None:
        script = os.path.join("scripts", "diagnostic", "validate_routes.py")
        subprocess.run([sys.executable, script])
