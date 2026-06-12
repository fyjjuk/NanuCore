"""Plugin: Repomix Stats"""
import subprocess
import sys
import os
from core.plugin.interface import UtilityPlugin

class RepomixStatsPlugin(UtilityPlugin):
    @property
    def name(self) -> str:
        return "Repomix Stats"
    
    @property
    def description(self) -> str:
        return "Muestra estadísticas de tokens"
    
    @property
    def category(self) -> str:
        return "repomix"
    
    def run(self) -> None:
        script = os.path.join("scripts", "cli.py")
        result = subprocess.run([sys.executable, script, "repomix-stats"], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"❌ Error: {result.stderr}")
