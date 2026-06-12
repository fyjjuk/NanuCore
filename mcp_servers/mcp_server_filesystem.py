import sys
import json

def run_tool(tool, args):
    if tool == "read":
        # Simulación de lectura
        return {"content": "Contenido del archivo simulado"}
    return {"error": "Tool not found"}

if __name__ == "__main__":
    tool = sys.argv[1]
    args = json.loads(sys.argv[2])
    print(json.dumps(run_tool(tool, args)))
