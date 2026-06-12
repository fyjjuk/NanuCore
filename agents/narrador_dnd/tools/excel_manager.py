#!/usr/bin/env python3
import json
import os
import sys
import pandas as pd
from typing import Dict, Any

WORKSPACE = os.path.join(os.path.dirname(__file__), "..", "workspace", "inventories")
os.makedirs(WORKSPACE, exist_ok=True)

def get_inventory_path(campaign: str = "main") -> str:
    safe = "".join(c for c in campaign if c.isalnum() or c in "._-")
    return os.path.join(WORKSPACE, f"{safe}.xlsx")

def add_item(campaign: str, item: str, quantity: int = 1) -> str:
    path = get_inventory_path(campaign)
    if os.path.exists(path):
        df = pd.read_excel(path)
    else:
        df = pd.DataFrame(columns=["Item", "Cantidad"])
    if item in df["Item"].values:
        df.loc[df["Item"] == item, "Cantidad"] += quantity
    else:
        df.loc[len(df)] = [item, quantity]
    df.to_excel(path, index=False)
    return f"✅ Añadido {quantity}x {item}"

def show_inventory(campaign: str = "main") -> str:
    path = get_inventory_path(campaign)
    if not os.path.exists(path):
        return "📦 Inventario vacío"
    df = pd.read_excel(path)
    if df.empty:
        return "📦 Inventario vacío"
    lines = ["📦 **Inventario**", ""]
    for _, row in df.iterrows():
        lines.append(f"- {row['Item']}: {row['Cantidad']}")
    return "\n".join(lines)

def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    action = input_data.get("action", "")
    campaign = input_data.get("campaign", "main")
    if action == "add":
        item = input_data.get("item", "")
        qty = int(input_data.get("quantity", 1))
        result = add_item(campaign, item, qty)
    elif action == "show":
        result = show_inventory(campaign)
    else:
        result = "Acciones: add, show"
    return {"result": result}

if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    result = run(args)
    print(json.dumps(result))
