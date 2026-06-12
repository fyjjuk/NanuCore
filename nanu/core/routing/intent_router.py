from pathlib import Path
import re
import yaml
from typing import Dict, Any, Optional
from nanu.core.agent import Agent

class IntentRouter:
    """Clasifica la intención del usuario y selecciona la ruta YAML adecuada."""
    
    def route(self, agent: Agent, user_input: str, threshold: float = 0.2) -> Optional[Dict[str, Any]]:
        """Retorna la ruta que mejor coincide o None."""
        user_lower = user_input.lower().strip()
        best_route = None
        best_score = 0.0
        
        # Cargar rutas desde el directorio del agente
        routes_dir = Path(agent.config_path).parent / "routes"
        if not routes_dir.exists():
            return None
        
        for yaml_file in routes_dir.glob("*.yaml"):
            with open(yaml_file, 'r', encoding='utf-8') as f:
                route = yaml.safe_load(f)
                if not route or 'route_id' not in route:
                    continue
                desc = route.get('description', '').lower()
                # Dividir descripción en palabras clave
                keywords = re.split(r'[, ]+', desc)
                matches = 0
                for kw in keywords:
                    if kw and kw in user_lower:
                        matches += 1
                        # Bono si la palabra clave es exactamente igual al input (útil para comandos cortos)
                        if kw == user_lower:
                            matches += 0.3
                if matches > 0:
                    # Score normalizado con bono máximo 0.3 extra
                    score = matches / (len(keywords) + 0.3)  # ajuste para no superar 1
                    if score > best_score:
                        best_score = score
                        best_route = route
        
        # Debug: mostrar scores (opcional, puedes eliminarlo después)
        if best_route:
            print(f"[DEBUG] Mejor ruta: {best_route['route_id']} (score={best_score:.2f})")
        
        if best_route and best_score >= threshold:
            return best_route
        return None
