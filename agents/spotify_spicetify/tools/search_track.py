#!/usr/bin/env python3
import subprocess
import sys
import json
import shutil
import re
import time
import urllib.parse
import os
from pathlib import Path

def find_spotify() -> str | None:
    """
    Busca el binario de Spotify en múltiples ubicaciones comunes.
    """
    # Posibles ubicaciones del binario de Spotify
    possible_paths = [
        os.path.expanduser("~/.local/share/spotify-launcher/install/usr/share/spotify/spotify"),
        os.path.expanduser("~/.spotify/spotify"),
        "/opt/spotify/spotify",
        "/usr/bin/spotify",
        "/usr/local/bin/spotify",
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    # Buscar con shutil.which (PATH)
    which_path = shutil.which("spotify")
    if which_path:
        return which_path
    
    # Buscar spotify-launcher
    launcher = shutil.which("spotify-launcher")
    if launcher:
        return launcher
    
    return None

def validate_query(query: str) -> bool:
    """Verifica que la consulta solo contenga caracteres seguros."""
    pattern = r'^[\w\sáéíóúñÑüÜ.,:;()\-&+]+$'
    if not re.match(pattern, query, re.UNICODE):
        return False
    if len(query) > 200:
        return False
    return True

def search(query):
    if not query:
        return "❌ No se detectó qué buscar"
    
    # Limpiar la consulta eliminando palabras clave iniciales
    original_query = query
    query = re.sub(r'^(busca|buscar|reproduce|reproducir|pon|toca)\s+', '', query.lower(), flags=re.IGNORECASE)
    
    if not query:
        query = original_query
    
    if not validate_query(query):
        return "❌ La consulta contiene caracteres no permitidos o es demasiado larga"
    
    print(f"[DEBUG] Búsqueda limpia: {query}", file=sys.stderr)
    
    spotify_path = find_spotify()
    if not spotify_path:
        return "❌ Spotify no encontrado. ¿Está instalado?"
    
    print(f"[DEBUG] Spotify encontrado en: {spotify_path}", file=sys.stderr)
    
    encoded_query = urllib.parse.quote(query, safe='')
    
    try:
        # Si es spotify-launcher, usar el comando con argumentos especiales
        if "spotify-launcher" in spotify_path:
            # spotify-launcher abre la URI directamente
            subprocess.run([spotify_path, f"spotify:search:{encoded_query}"], timeout=5, capture_output=True)
        else:
            # Spotify normal
            uri = f"spotify:search:{encoded_query}"
            subprocess.run([spotify_path, uri], timeout=5, capture_output=True)
        
        time.sleep(1)
        if shutil.which("playerctl"):
            subprocess.run(["playerctl", "--player=spotify", "play"], capture_output=True)
        return f"🎵 Buscando: {query}"
    except Exception as e:
        return f"🔍 Buscando: {query} (error: {e})"

def main():
    if len(sys.argv) < 2:
        print("❌ Se requiere consulta")
        sys.exit(1)
    try:
        args = json.loads(sys.argv[1])
        query = args.get("query", "")
        result = search(query)
        print(result)
    except json.JSONDecodeError:
        result = search(" ".join(sys.argv[1:]))
        print(result)

if __name__ == "__main__":
    main()
