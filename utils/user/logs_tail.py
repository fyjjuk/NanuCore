"""Plugin: Logs Tail"""
import subprocess
import sys
import os
from core.plugin.interface import UtilityPlugin

class LogsTailPlugin(UtilityPlugin):
    @property
    def name(self) -> str:
        return "Logs Tail"
    
    @property
    def description(self) -> str:
        return "Muestra logs en tiempo real"
    
    @property
    def category(self) -> str:
        return "user"
    
    def run(self) -> None:
        script = os.path.join("scripts", "user", "logs_tail.py")
        subprocess.run([sys.executable, script])
