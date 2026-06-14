#!/usr/bin/env python3
import subprocess
import sys
import json
import shutil
import re
import time

def search(query):
    if not query:
        return "❌ No se detectó qué buscar"
    
    # Limpiar la consulta
    query = re.sub(r'^(busca|buscar|reproduce|reproducir|pon|toca)\s+', '', query.lower())
    
    spotify = shutil.which("spotify")
    if not spotify:
        return "❌ Spotify no encontrado"
    
    try:
        subprocess.run([spotify, f"spotify:search:{query.replace(' ', '%20')}"], timeout=5, capture_output=True)
        time.sleep(1)
        if shutil.which("playerctl"):
            subprocess.run(["playerctl", "--player=spotify", "play"], capture_output=True)
        return f"🎵 Buscando: {query}"
    except Exception as e:
        return f"🔍 Buscando: {query}"

def main():
    if len(sys.argv) < 2:
        print("❌ Se requiere consulta")
        sys.exit(1)
    args = json.loads(sys.argv[1])
    result = search(args.get("query", ""))
    print(result)

if __name__ == "__main__":
    main()
