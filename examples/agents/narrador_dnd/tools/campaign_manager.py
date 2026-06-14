#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

WORKSPACE = os.path.join(os.path.dirname(__file__), "..", "workspace", "campaigns")
os.makedirs(WORKSPACE, exist_ok=True)

def get_campaign_path(campaign_name: str) -> str:
    safe_name = "".join(c for c in campaign_name if c.isalnum() or c in "._-")
    return os.path.join(WORKSPACE, f"{safe_name}.json")

def default_campaign_state(name: str) -> Dict:
    return {
        "name": name,
        "active": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "current_session": 1,
        "session_notes": [],
        "active_quests": [],
        "completed_quests": []
    }

def get_state(campaign_name: str = "main") -> Dict:
    path = get_campaign_path(campaign_name)
    if not os.path.exists(path):
        return default_campaign_state(campaign_name)
    with open(path, "r") as f:
        return json.load(f)

def save_state(state: Dict) -> str:
    path = get_campaign_path(state["name"])
    state["updated_at"] = datetime.now().isoformat()
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
    return f"✅ Campaña guardada"

def add_quest(campaign_name: str, quest_name: str) -> str:
    state = get_state(campaign_name)
    if quest_name not in state["active_quests"]:
        state["active_quests"].append(quest_name)
        save_state(state)
        return f"📜 Quest '{quest_name}' añadida"
    return f"⚠️ Quest ya existe"

def show_status(campaign_name: str = "main") -> str:
    state = get_state(campaign_name)
    active = ', '.join(state['active_quests']) if state['active_quests'] else 'Ninguna'
    return f"📖 Campaña: {state['name']}\n   Quests activas: {active}\n   Completadas: {len(state['completed_quests'])}"

def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    action = input_data.get("action", "")
    campaign = input_data.get("campaign", "main")
    if action == "add_quest":
        quest = input_data.get("quest", "")
        result = add_quest(campaign, quest)
    elif action == "status":
        result = show_status(campaign)
    else:
        result = "Acciones: add_quest, status"
    return {"result": result}

if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    result = run(args)
    print(json.dumps(result))
