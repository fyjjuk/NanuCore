"""Cliente para Groq con soporte para múltiples API keys."""
import aiohttp
import os
from typing import Dict, Any, Optional
from .base import LLMClient
from nanu.core.utils.sanitize import sanitize_error

class GroqClient(LLMClient):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_keys = self._load_api_keys()
        self.current_key_index = 0
    
    def _load_api_keys(self) -> list:
        keys = []
        for key_name, value in os.environ.items():
            if key_name.startswith('GROQ_API_KEY'):
                if value and value.strip():
                    keys.append(value.strip())
        single_key = os.environ.get('GROQ_API_KEY')
        if single_key and single_key.strip() and single_key not in keys:
            keys.append(single_key.strip())
        return keys
    
    def _get_current_key(self) -> Optional[str]:
        if not self.api_keys:
            return None
        return self.api_keys[self.current_key_index % len(self.api_keys)]
    
    def _rotate_key(self):
        self.current_key_index += 1
        print(f"[Groq] Rotando a API key {self.current_key_index + 1}/{len(self.api_keys)}")
    
    async def available(self) -> bool:
        return len(self.api_keys) > 0
    
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        if not self.api_keys:
            return "Error: No hay API keys de Groq configuradas"
        
        max_retries = len(self.api_keys)
        for attempt in range(max_retries):
            api_key = self._get_current_key()
            if not api_key:
                break
            
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get('temperature', self.temperature),
                "max_tokens": kwargs.get('max_tokens', self.max_tokens),
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, headers=headers, timeout=self.timeout) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            try:
                                return data['choices'][0]['message']['content']
                            except (KeyError, IndexError):
                                return "Error: Respuesta inesperada de Groq"
                        elif resp.status == 429:
                            print(f"[Groq] Key {attempt + 1} rate limit, rotando...")
                            self._rotate_key()
                            continue
                        else:
                            error_text = await resp.text()
                            sanitized = sanitize_error(error_text)
                            return f"Error: Groq respondió con {resp.status}: {sanitized}"
            except Exception as e:
                print(f"[Groq] Error con key {attempt + 1}: {e}")
                self._rotate_key()
                continue
        
        return "Error: Todas las API keys de Groq fallaron"
