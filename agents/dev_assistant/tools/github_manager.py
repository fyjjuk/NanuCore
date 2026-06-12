#!/usr/bin/env python3
"""
GitHub manager - Herramientas para interactuar con GitHub.
"""

import json
import sys
import os
from typing import Dict, Any

# Intentar importar PyGithub
try:
    from github import Github
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

def get_github_client():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return None
    return Github(token)

def list_repos(limit: int = 10) -> str:
    if not GITHUB_AVAILABLE:
        return "❌ PyGithub no instalado. Instala con: pip install PyGithub"
    client = get_github_client()
    if not client:
        return "❌ GITHUB_TOKEN no configurada en variables de entorno"
    repos = []
    for repo in client.get_user().get_repos()[:limit]:
        repos.append(f"- [{repo.name}]({repo.html_url}) - ⭐ {repo.stargazers_count}")
    return "\n".join(repos) if repos else "No se encontraron repositorios"

def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    action = input_data.get("action", "")
    if action == "list_repos":
        limit = int(input_data.get("limit", 10))
        result = list_repos(limit)
    else:
        result = "Acciones disponibles: list_repos"
    return {"result": result}

if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    result = run(args)
    print(json.dumps(result))
