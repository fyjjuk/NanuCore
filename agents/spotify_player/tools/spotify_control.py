#!/usr/bin/env python3
import subprocess
import sys
import json
import shutil
import time

def run_spotify_command(action: str) -> str:
    """Ejecuta comandos de control de Spotify."""
    if not shutil.which("playerctl"):
        return "❌ 'playerctl' no está instalado. Instálalo con: sudo dnf install playerctl"
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            if action == "play":
                subprocess.run(["playerctl", "--player=spotify", "play"], check=True, capture_output=True)
                return "▶️ Reproduciendo"
            elif action == "pause":
                subprocess.run(["playerctl", "--player=spotify", "pause"], check=True, capture_output=True)
                return "⏸️ Pausado"
            elif action == "next":
                subprocess.run(["playerctl", "--player=spotify", "next"], check=True, capture_output=True)
                return "⏭️ Siguiente canción"
            elif action == "previous":
                subprocess.run(["playerctl", "--player=spotify", "previous"], check=True, capture_output=True)
                return "⏮️ Canción anterior"
            elif action == "status":
                result = subprocess.run(["playerctl", "--player=spotify", "status"], capture_output=True, text=True)
                status = result.stdout.strip()
                if status == "Playing":
                    return "▶️ Reproduciendo"
                elif status == "Paused":
                    return "⏸️ Pausado"
                else:
                    return "⏹️ Detenido o no disponible"
            else:
                return f"❌ Acción desconocida: {action}"
        except subprocess.CalledProcessError as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            if "No players found" in str(e.stderr):
                return "❌ Spotify no está abierto. Ábrelo primero."
            return f"❌ Error controlando Spotify: {e.stderr if e.stderr else str(e)}"
        except Exception as e:
            return f"❌ Error inesperado: {str(e)}"
    return "❌ No se pudo completar la acción después de varios intentos."

def main():
    if len(sys.argv) < 2:
        print("Uso: python spotify_control.py '{\"action\": \"play\"}'")
        sys.exit(1)
    args = json.loads(sys.argv[1])
    action = args.get("action", "")
    result = run_spotify_command(action)
    print(result)

if __name__ == "__main__":
    main()
