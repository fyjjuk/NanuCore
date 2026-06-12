#!/usr/bin/env python3
"""
Gestión de fichas de personaje para D&D.
"""

import json
import os
import sys
from typing import Dict, Any

CHARACTERS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "characters")
os.makedirs(CHARACTERS_DIR, exist_ok=True)


def get_character_path(character_name: str) -> str:
    """Obtiene la ruta del archivo de personaje."""
    safe_name = "".join(c for c in character_name if c.isalnum() or c in "._-")
    return os.path.join(CHARACTERS_DIR, f"{safe_name}.json")


def default_character_sheet(name: str) -> Dict:
    """Retorna una ficha de personaje por defecto."""
    return {
        "name": name,
        "level": 1,
        "class": "",
        "race": "",
        "background": "",
        "stats": {
            "STR": 10, "DEX": 10, "CON": 10,
            "INT": 10, "WIS": 10, "CHA": 10
        },
        "hp": {"current": 10, "max": 10},
        "ac": 10,
        "proficiency": 2,
        "equipment": [],
        "spells": [],
        "notes": "",
        "created_at": "",
        "updated_at": ""
    }


def create_character(name: str, character_class: str = "", race: str = "") -> str:
    """Crea un nuevo personaje."""
    sheet = default_character_sheet(name)
    sheet["class"] = character_class
    sheet["race"] = race
    sheet["created_at"] = __import__("datetime").datetime.now().isoformat()
    sheet["updated_at"] = sheet["created_at"]
    
    file_path = get_character_path(name)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sheet, f, indent=2, ensure_ascii=False)
    
    return f"✅ Personaje '{name}' creado con éxito"


def get_character(name: str) -> Dict:
    """Obtiene los datos de un personaje."""
    file_path = get_character_path(name)
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_stat(name: str, stat: str, value: int) -> str:
    """Actualiza una estadística del personaje."""
    sheet = get_character(name)
    if not sheet:
        return f"❌ Personaje '{name}' no encontrado"
    
    if stat.upper() not in sheet["stats"]:
        return f"❌ Estadística '{stat}' no válida. Opciones: STR, DEX, CON, INT, WIS, CHA"
    
    sheet["stats"][stat.upper()] = value
    sheet["updated_at"] = __import__("datetime").datetime.now().isoformat()
    
    with open(get_character_path(name), "w", encoding="utf-8") as f:
        json.dump(sheet, f, indent=2, ensure_ascii=False)
    
    return f"✅ {stat.upper()} actualizado a {value} para '{name}'"


def update_hp(name: str, current: int = None, max_hp: int = None) -> str:
    """Actualiza los HP del personaje."""
    sheet = get_character(name)
    if not sheet:
        return f"❌ Personaje '{name}' no encontrado"
    
    if max_hp is not None:
        sheet["hp"]["max"] = max_hp
    if current is not None:
        sheet["hp"]["current"] = current
    
    sheet["updated_at"] = __import__("datetime").datetime.now().isoformat()
    
    with open(get_character_path(name), "w", encoding="utf-8") as f:
        json.dump(sheet, f, indent=2, ensure_ascii=False)
    
    return f"✅ HP actualizado para '{name}': {sheet['hp']['current']}/{sheet['hp']['max']}"


def show_character(name: str) -> str:
    """Muestra la ficha de personaje."""
    sheet = get_character(name)
    if not sheet:
        return f"❌ Personaje '{name}' no encontrado"
    
    stats_display = " | ".join([f"{k}:{v}" for k, v in sheet["stats"].items()])
    
    return f"""
🎲 **{sheet['name']}** (Nivel {sheet['level']})
   Clase: {sheet['class']} | Raza: {sheet['race']}
   HP: {sheet['hp']['current']}/{sheet['hp']['max']} | CA: {sheet['ac']}
   Stats: {stats_display}
   Equipo: {', '.join(sheet['equipment']) if sheet['equipment'] else 'Ninguno'}
   Notas: {sheet['notes'][:100]}...
"""


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Punto de entrada para la herramienta."""
    action = input_data.get("action", "")
    name = input_data.get("name", "")
    
    if action == "create":
        char_class = input_data.get("class", "")
        race = input_data.get("race", "")
        result = create_character(name, char_class, race)
    elif action == "show":
        result = show_character(name)
    elif action == "update_stat":
        stat = input_data.get("stat", "")
        value = int(input_data.get("value", 10))
        result = update_stat(name, stat, value)
    elif action == "update_hp":
        current = input_data.get("current")
        max_hp = input_data.get("max")
        result = update_hp(name, current, max_hp)
    else:
        result = f"Acciones disponibles: create, show, update_stat, update_hp"
    
    return {"result": result}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    result = run(args)
    print(json.dumps(result))
