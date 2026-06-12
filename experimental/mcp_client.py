import subprocess
import json
import time
import os
from core.logger import logger

class MCPClient:
    def __init__(self):
        # Usar ruta absoluta relativa al archivo
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.server_path = os.path.join(base_dir, "mcp_servers")

    def call_tool(self, server_name: str, tool_name: str, arguments: dict):
        start_time = time.perf_counter()
        try:
            script_path = os.path.join(self.server_path, f"mcp_server_{server_name}.py")
            if not os.path.exists(script_path):
                return {"error": f"Servidor MCP no encontrado: {script_path}"}

            process = subprocess.run(
                ["python", script_path, tool_name, json.dumps(arguments)],
                capture_output=True, text=True, timeout=30
            )
            success = process.returncode == 0
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            logger.info(f"MCP Tool execution: {tool_name}", extra={"duration_ms": duration_ms, "success": success})
            return json.loads(process.stdout) if success else {"error": process.stderr}
        except Exception as e:
            return {"error": str(e)}
