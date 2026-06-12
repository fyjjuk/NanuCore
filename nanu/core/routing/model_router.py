"""Decide si usar modelo ligero o pesado basado en heurísticas."""
from typing import Dict, Any

class ModelRouter:
    """Selecciona el tipo de modelo (light/heavy) según la entrada y la ruta."""
    
    def decide(self, user_input: str, route: Dict[str, Any]) -> str:
        """Retorna 'light' o 'heavy'."""
        # Si la ruta requiere herramientas pesadas, usar heavy
        if route.get('tools_allowed'):
            return 'heavy'
        
        # Si el mensaje es largo (>300 caracteres) o tiene bloques de código
        if len(user_input) > 300:
            return 'heavy'
        
        if "```" in user_input:
            return 'heavy'
        
        # Por defecto, light
        return 'light'
