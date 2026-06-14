#!/usr/bin/env python3
import subprocess
import sys
import json
import shutil

def set_volume(value):
    try:
        val = int(value)
    except:
        return "❌ Valor no válido"
    
    # Obtener volumen actual si es necesario (para deltas)
    if val < 0 or val > 100:
        current = 50
        if shutil.which("playerctl"):
            try:
                vol = subprocess.run(["playerctl", "--player=spotify", "volume"], capture_output=True, text=True).stdout.strip()
                if vol:
                    current = int(float(vol) * 100)
            except:
                pass
        val = current + val
    
    val = max(0, min(100, val))
    
    try:
        subprocess.run(["playerctl", "--player=spotify", "volume", str(val/100)], check=True, capture_output=True)
        return f"🔊 Volumen: {val}%"
    except Exception as e:
        return f"❌ Error: {e}"

def main():
    if len(sys.argv) < 2:
        print("❌ Se requiere valor")
        sys.exit(1)
    args = json.loads(sys.argv[1])
    result = set_volume(args.get("value", 50))
    print(result)

if __name__ == "__main__":
    main()
