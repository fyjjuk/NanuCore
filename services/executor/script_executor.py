import subprocess
import json
import os
import re
from typing import Dict, Any
from core.logger import logger
from .base import BaseExecutor

class ScriptExecutor(BaseExecutor):
    """Ejecuta rutas de script (herramientas nativas del agente)."""
    
    def execute(self, agent, intent: Dict[str, Any], query: str, router, rag_engine) -> str:
        script_path = intent.get("script_path")
        script_args = intent.get("script_args", {})
        
        # Reemplazar placeholders en script_args
        processed_args = {}
        for key, value in script_args.items():
            if isinstance(value, str) and "{user_input}" in value:
                processed_args[key] = value.replace("{user_input}", query)
            else:
                processed_args[key] = value
        
        # Construir ruta absoluta al script dentro del agente
        if script_path and not os.path.isabs(script_path):
            # Buscar primero en el directorio del agente
            agent_dir = os.path.join("agents", agent.id)
            full_path = os.path.join(agent_dir, script_path)
            
            if not os.path.exists(full_path):
                # Si no existe, buscar en la biblioteca global
                full_path = os.path.join("tools", "native", os.path.basename(script_path))
        
        if not full_path or not os.path.exists(full_path):
            return f"Error: Herramienta no encontrada: {script_path}"
        
        try:
            if processed_args:
                args_str = json.dumps(processed_args)
                result = subprocess.run(["python", full_path, args_str], capture_output=True, text=True, timeout=10)
            else:
                result = subprocess.run(["python", full_path, query], capture_output=True, text=True, timeout=10)
            
            output = result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr}"
            return output
        except subprocess.TimeoutExpired:
            return "Error: La herramienta tardó demasiado en responder"
        except Exception as e:
            return f"Error: {str(e)}"
