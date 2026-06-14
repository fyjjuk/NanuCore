#!/usr/bin/env python3
"""
Gestión de inventarios por personaje usando archivos Markdown Table.
Soporta extracción de nombre de personaje de frases naturales.
"""

import os
import sys
import json
import re
from typing import Dict, Any, List, Tuple

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "workspace", "inventories")
os.makedirs(DATA_DIR, exist_ok=True)

def get_inventory_path(character_name: str) -> str:
    safe = "".join(c for c in character_name if c.isalnum() or c in "._-")
    return os.path.join(DATA_DIR, f"{safe}.md")

def parse_inventory_table(content: str) -> List[Tuple[str, str, str, str, str]]:
    rows = []
    lines = content.split('\n')
    for line in lines:
        if line.startswith('|') and '|' in line:
            if re.match(r'\|[\s\-:]+\|', line):
                continue
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if len(cells) >= 2 and cells[0] != 'Item':
                while len(cells) < 5:
                    cells.append('')
                rows.append(tuple(cells[:5]))
    return rows

def extract_character_name(user_input: str) -> str:
    """Extrae el nombre del personaje de frases como 'añade item al inventario de Gandalf'"""
    patterns = [
        r'inventario de ([A-Za-z][A-Za-z0-9_]*)',
        r'para ([A-Za-z][A-Za-z0-9_]*)',
        r'a ([A-Za-z][A-Za-z0-9_]*)',
    ]
    for pattern in patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            return match.group(1)
    # Si no se encuentra, asumir que la entrada es solo el nombre
    return user_input.strip()

def extract_item_name(user_input: str) -> str:
    """Extrae el nombre del item de frases como 'añade poción de curación'"""
    # Remover partes comunes
    patterns = [
        r'añade\s+(.+?)\s+(?:al inventario|para|a)',
        r'agrega\s+(.+?)\s+(?:al inventario|para|a)',
        r'nuevo item\s+(.+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    # Fallback: tomar la frase completa después del verbo
    words = user_input.split()
    if len(words) > 1 and words[0].lower() in ('añade', 'agrega'):
        return ' '.join(words[1:])
    return user_input

def add_item(character_name: str, item: str, quantity: int = 1, 
             value: float = 0, weight: float = 0, notes: str = "") -> str:
    path = get_inventory_path(character_name)
    
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        rows = parse_inventory_table(content)
    else:
        rows = []
    
    found = False
    for i, row in enumerate(rows):
        if row[0].lower() == item.lower():
            new_qty = int(row[1]) + quantity
            rows[i] = (row[0], str(new_qty), row[2], row[3], row[4] if len(row) > 4 else '')
            found = True
            break
    
    if not found:
        rows.append((item, str(quantity), str(value), str(weight), notes))
    
    lines = ["| Item | Cantidad | Valor (gp) | Peso (lb) | Notas |"]
    lines.append("|------|----------|------------|-----------|-------|")
    for row in rows:
        lines.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |")
    
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    return f"✅ Añadido {quantity}x {item} al inventario de {character_name}"

def show_inventory(character_name: str) -> str:
    path = get_inventory_path(character_name)
    if not os.path.exists(path):
        return f"📦 **Inventario de {character_name}**\n\nNo hay items registrados."
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    rows = parse_inventory_table(content)
    if not rows:
        return f"📦 **Inventario de {character_name}**\n\nNo hay items registrados."
    
    return f"📦 **Inventario de {character_name}**\n\n{content}"

def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    action = input_data.get("action", "")
    # Si character es la frase completa, extraer nombre
    raw_char = input_data.get("character", "")
    character = extract_character_name(raw_char) if raw_char else ""
    item = input_data.get("item", "")
    # Si item es frase completa, extraer item
    if item and len(item.split()) > 2:
        item = extract_item_name(item)
    
    if action == "add":
        qty = int(input_data.get("quantity", 1))
        val = float(input_data.get("value", 0))
        w = float(input_data.get("weight", 0))
        notes = input_data.get("notes", "")
        result = add_item(character, item, qty, val, w, notes)
    elif action == "show":
        result = show_inventory(character)
    else:
        result = "Acciones: add, show"
    
    return {"result": result}

if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    result = run(args)
    print(json.dumps(result))
