#!/usr/bin/env python3
"""
Gestión de personajes usando archivos Markdown.
"""

import os
import sys
import json
import re
from datetime import datetime
from typing import Dict, Any

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "workspace", "characters")
os.makedirs(DATA_DIR, exist_ok=True)

def get_character_path(name: str) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in "._-")
    return os.path.join(DATA_DIR, f"{safe}.md")

def extract_name_from_input(user_input: str) -> str:
    """Extrae el nombre del personaje de frases como 'crea un personaje llamado Aragorn'"""
    patterns = [
        r'crea un personaje llamado ["\']?([^"\' ]+)["\']?',
        r'personaje llamado ["\']?([^"\' ]+)["\']?',
        r'llamado ["\']?([^"\' ]+)["\']?',
        r'^([A-Za-z][A-Za-z0-9_]+)$',  # Nombre simple
    ]
    for pattern in patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            return match.group(1)
    # Si no coincide, tomar la primera palabra
    return user_input.split()[0] if user_input.split() else user_input

def extract_class_from_input(user_input: str) -> str:
    patterns = [r'clase\s+(\w+)', r'class\s+(\w+)']
    for pattern in patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            return match.group(1)
    return ""

def extract_race_from_input(user_input: str) -> str:
    patterns = [r'raza\s+(\w+)', r'race\s+(\w+)']
    for pattern in patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            return match.group(1)
    return ""

def create_character(user_input: str) -> str:
    name = extract_name_from_input(user_input)
    char_class = extract_class_from_input(user_input)
    race = extract_race_from_input(user_input)
    
    if not name:
        return "❌ No se pudo extraer el nombre del personaje"
    
    path = get_character_path(name)
    if os.path.exists(path):
        return f"⚠️ El personaje '{name}' ya existe"
    
    content = f"""# {name}

## Atributos
- **Clase:** {char_class}
- **Raza:** {race}
- **Nivel:** 1

### Características
- **STR:** 10
- **DEX:** 10
- **CON:** 10
- **INT:** 10
- **WIS:** 10
- **CHA:** 10

## Combate
- **HP:** 10/10
- **CA:** 10
- **Iniciativa:** 0

## Equipo


## Notas

"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return f"✅ Personaje '{name}' creado (Clase: {char_class or 'sin especificar'}, Raza: {race or 'sin especificar'})"

def show_character(user_input: str) -> str:
    name = extract_name_from_input(user_input)
    if not name:
        return "❌ No se pudo extraer el nombre del personaje"
    
    path = get_character_path(name)
    if not os.path.exists(path):
        return f"❌ Personaje '{name}' no encontrado"
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Añadir enlace al inventario
    inventory_link = f"\n\n📦 [Ver inventario de {name}](inventario:{name})"
    
    return content + inventory_link

def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    action = input_data.get("action", "")
    user_input = input_data.get("input", "")
    
    if action == "create":
        result = create_character(user_input)
    elif action == "show":
        result = show_character(user_input)
    else:
        result = "Acciones: create, show"
    
    return {"result": result}

if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    result = run(args)
    print(json.dumps(result))
