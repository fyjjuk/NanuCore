#!/usr/bin/env python3
import subprocess
import sys
import json
import shutil
import urllib.parse

def search_and_play(query: str) -> str:
    """Busca y reproduce una canción o artista en Spotify."""
    if not query or query.strip() == "":
        return "❌ No se detectó ninguna canción o artista"
    
    # Encontrar comando de Spotify
    spotify_cmd = shutil.which("spotify")
    if not spotify_cmd:
        spotify_cmd = shutil.which("flatpak")
        if spotify_cmd:
            spotify_cmd = [spotify_cmd, "run", "com.spotify.Client"]
        else:
            return "❌ No se encontró Spotify instalado"
    else:
        spotify_cmd = [spotify_cmd]
    
    encoded_query = urllib.parse.quote(query.strip())
    uri = f"spotify:search:{encoded_query}"
    
    try:
        subprocess.run(spotify_cmd + [uri], timeout=5, capture_output=True)
        return f"🔍 Buscando: {query}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def main():
    if len(sys.argv) > 1:
        try:
            args = json.loads(sys.argv[1])
            query = args.get("query", "")
            result = search_and_play(query)
            print(result)
        except:
            query = " ".join(sys.argv[1:])
            result = search_and_play(query)
            print(result)
    else:
        print("❌ Se requiere una consulta")

if __name__ == "__main__":
    main()
