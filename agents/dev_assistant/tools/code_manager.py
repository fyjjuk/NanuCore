#!/usr/bin/env python3
"""
Code manager - Herramientas para revisión de código.
"""

import json
import sys
from typing import Dict, Any

def analyze_code(code: str) -> str:
    lines = code.split('\n')
    issues = []
    for i, line in enumerate(lines, 1):
        if len(line) > 100:
            issues.append(f"- Línea {i}: demasiado larga ({len(line)} > 100)")
        if "TODO" in line.upper():
            issues.append(f"- Línea {i}: TODO pendiente")
        if "FIXME" in line.upper():
            issues.append(f"- Línea {i}: FIXME pendiente")
    if not issues:
        return "✅ No se encontraron problemas evidentes"
    return "⚠️ Problemas encontrados:\n" + "\n".join(issues)

def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    action = input_data.get("action", "")
    if action == "analyze":
        code = input_data.get("code", "")
        result = analyze_code(code)
    else:
        result = "Acciones disponibles: analyze"
    return {"result": result}

if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    result = run(args)
    print(json.dumps(result))
