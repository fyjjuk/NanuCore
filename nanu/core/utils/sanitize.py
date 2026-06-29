"""Utilidades de sanitización para mensajes de error."""
import re

def sanitize_error(text: str) -> str:
    """
    Elimina posibles claves API o credenciales de un mensaje de error.
    """
    if not text:
        return text
    
    # Patrones comunes de API keys
    patterns = [
        r'[A-Za-z0-9]{32,}',           # Cadenas largas alfanuméricas
        r'sk-[A-Za-z0-9-_]+',          # OpenAI/OpenRouter style
        r'AIza[A-Za-z0-9-_]+',         # Gemini API key
        r'Bearer\s+[A-Za-z0-9\-_\.]+', # Bearer tokens
        r'api[_-]?key[=:]\s*[A-Za-z0-9]+', # Key=value
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, '[REDACTED]', text, flags=re.IGNORECASE)
    
    # Limitar longitud
    if len(text) > 200:
        text = text[:197] + '...'
    
    return text
