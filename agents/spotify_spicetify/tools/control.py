#!/usr/bin/env python3
import subprocess
import sys
import json
import shutil

def run(action):
    if not shutil.which("playerctl"):
        return "❌ playerctl no instalado"
    try:
        if action == "play":
            subprocess.run(["playerctl", "--player=spotify", "play"], check=True, capture_output=True)
            return "▶️ Reproduciendo"
        elif action == "pause":
            subprocess.run(["playerctl", "--player=spotify", "pause"], check=True, capture_output=True)
            return "⏸️ Pausado"
        elif action == "next":
            subprocess.run(["playerctl", "--player=spotify", "next"], check=True, capture_output=True)
            return "⏭️ Siguiente"
        elif action == "previous":
            subprocess.run(["playerctl", "--player=spotify", "previous"], check=True, capture_output=True)
            return "⏮️ Anterior"
        elif action == "status":
            title = subprocess.run(["playerctl", "--player=spotify", "metadata", "xesam:title"], capture_output=True, text=True).stdout.strip()
            artist = subprocess.run(["playerctl", "--player=spotify", "metadata", "xesam:artist"], capture_output=True, text=True).stdout.strip()
            if title:
                return f"▶️ {title} - {artist}" if artist else f"▶️ {title}"
            return "⏹️ No hay canción"
    except subprocess.CalledProcessError:
        return "❌ Spotify no está reproduciendo"
    return f"✅ {action}"

def main():
    if len(sys.argv) < 2:
        print("❌ Se requiere acción")
        sys.exit(1)
    args = json.loads(sys.argv[1])
    result = run(args.get("action", ""))
    print(result)

if __name__ == "__main__":
    main()
