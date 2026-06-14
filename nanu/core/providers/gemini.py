"""Cliente para Google Gemini con soporte para múltiples API keys."""
import aiohttp
import os
import re
from typing import Dict, Any, Optional
from .base import LLMClient

class GeminiClient(LLMClient):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_keys = self._load_api_keys()
        self.current_key_index = 0
    
    def _load_api_keys(self) -> list:
        """Carga múltiples API keys de variables de entorno."""
        keys = []
        # Buscar GOOGLE_API_KEY_1, GOOGLE_API_KEY_2, etc.
        for key_name, value in os.environ.items():
            if key_name.startswith('GOOGLE_API_KEY'):
                if value and value.strip():
                    keys.append(value.strip())
        # También buscar la variable simple GOOGLE_API_KEY
        single_key = os.environ.get('GOOGLE_API_KEY')
        if single_key and single_key.strip() and single_key not in keys:
            keys.append(single_key.strip())
        return keys
    
    def _get_current_key(self) -> Optional[str]:
        if not self.api_keys:
            return None
        return self.api_keys[self.current_key_index % len(self.api_keys)]
    
    def _rotate_key(self):
        self.current_key_index += 1
        print(f"[Gemini] Rotando a API key {self.current_key_index + 1}/{len(self.api_keys)}")
    
    async def available(self) -> bool:
        return len(self.api_keys) > 0
    
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        if not self.api_keys:
            return "Error: No hay API keys de Gemini configuradas"
        
        max_retries = len(self.api_keys)
        for attempt in range(max_retries):
            api_key = self._get_current_key()
            if not api_key:
                break
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={api_key}"
            
            # Construir contenido
            contents = []
            if system_prompt:
                contents.append({"role": "user", "parts": [{"text": system_prompt}]})
                contents.append({"role": "model", "parts": [{"text": "Entendido."}]})
            contents.append({"role": "user", "parts": [{"text": prompt}]})
            
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": kwargs.get('temperature', self.temperature),
                    "maxOutputTokens": kwargs.get('max_tokens', self.max_tokens),
                    "topP": 0.95,
                }
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, timeout=self.timeout) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            try:
                                return data['candidates'][0]['content']['parts'][0]['text']
                            except (KeyError, IndexError):
                                return f"Error: Respuesta inesperada de Gemini"
                        elif resp.status == 429 or resp.status == 403:
                            # Rate limit o quota excedida, rotar key
                            print(f"[Gemini] Key {attempt + 1} falló con status {resp.status}, rotando...")
                            self._rotate_key()
                            continue
                        else:
                            return f"Error: Gemini respondió con {resp.status}"
            except Exception as e:
                print(f"[Gemini] Error con key {attempt + 1}: {e}")
                self._rotate_key()
                continue
        
        return "Error: Todas las API keys de Gemini fallaron"
