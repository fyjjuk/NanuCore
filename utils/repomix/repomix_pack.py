"""Plugin: Repomix Pack"""
import subprocess
import sys
import os
from core.plugin.interface import UtilityPlugin

class RepomixPackPlugin(UtilityPlugin):
    @property
    def name(self) -> str:
        return "Repomix Pack"
    
    @property
    def description(self) -> str:
        return "Empaqueta el repositorio en Markdown (IA Export)"
    
    @property
    def category(self) -> str:
        return "repomix"
    
    def run(self) -> None:
        script = os.path.join("scripts", "cli.py")
        result = subprocess.run([sys.executable, script, "repomix-config"], capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stdout)
            print(f"\n❌ Error: {result.stderr}")
            if "npx" in result.stderr:
                print("\n💡 Sugerencia: Instala npx con 'npm install -g npx'")
        else:
            print(result.stdout)
