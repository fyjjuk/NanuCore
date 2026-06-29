#!/usr/bin/env python3
import subprocess
import sys
import json
import shutil
import re
import time
import urllib.parse

def validate_query(query: str) -> bool:
    """Verifica que la consulta solo contenga caracteres seguros."""
    # Solo letras (incluyendo acentuadas), números, espacios, y puntuación básica
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
    
    # Preservar acentos y caracteres especiales
    if not query:
        query = original_query
    
    # VALIDACIÓN DE SEGURIDAD
    if not validate_query(query):
        return "❌ La consulta contiene caracteres no permitidos o es demasiado larga"
    
    print(f"[DEBUG] Búsqueda limpia: {query}", file=sys.stderr)
    
    spotify = shutil.which("spotify")
    if not spotify:
        return "❌ Spotify no encontrado"
    
    # Codificar la consulta correctamente (preserva acentos)
    encoded_query = urllib.parse.quote(query, safe='')
    
    try:
        uri = f"spotify:search:{encoded_query}"
        subprocess.run([spotify, uri], timeout=5, capture_output=True)
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
