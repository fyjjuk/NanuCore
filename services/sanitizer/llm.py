import re
import requests
from core.logger import logger
from .base import BaseSanitizer

class LLMSanitizer(BaseSanitizer):
    def __init__(self, model: str = "phi3:mini", ollama_url: str = "http://localhost:11434/api/generate"):
        self.model = model
        self.ollama_url = ollama_url

    def clean(self, user_input: str) -> str:
        # Limpieza simple básica como respaldo
        simple = self._simple_clean(user_input)
        # Si la entrada es muy corta, no usar LLM
        if len(user_input) < 50:
            return simple
        prompt = f"""Limpia esta consulta eliminando muletillas, ruido y ambigüedades. Devuelve SOLO el texto limpio, sin explicaciones ni comillas.

Consulta: "{user_input}"
Texto limpio:"""
        try:
            response = requests.post(
                self.ollama_url,
                json={"model": self.model, "prompt": prompt, "stream": False, "options": {"temperature": 0.0, "num_predict": 200}},
                timeout=30
            )
            cleaned = response.json().get("response", "").strip()
            # Eliminar posibles prefijos residuales
            cleaned = re.sub(r'^(Texto limpio:|La consulta limpia es:|Claro, aquí está:)\s*', '', cleaned, flags=re.IGNORECASE)
            cleaned = cleaned.strip('"\'')
            logger.debug(f"LLMSanitizer: '{user_input[:30]}...' -> '{cleaned[:30]}...'")
            return cleaned if cleaned else simple
        except Exception as e:
            logger.warning(f"LLMSanitizer falló: {e}, usando limpieza simple")
            return simple

    def _simple_clean(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\x20-\x7EáéíóúñÑüÜ¿?¡!]', '', text)
        return text
