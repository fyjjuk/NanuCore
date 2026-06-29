"""Cliente para OpenRouter API."""
import aiohttp
import os
from typing import Dict, Any, Optional
from .base import LLMClient
from nanu.core.utils.sanitize import sanitize_error

class OpenRouterClient(LLMClient):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key') or os.environ.get('OPENROUTER_API_KEY')
        self.base_url = config.get('base_url', 'https://openrouter.ai/api/v1')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/fyjjuk/NanuCore",
            "X-Title": "NanuCore"
        }
    
    async def available(self) -> bool:
        if not self.api_key:
            return False
        try:
            url = f"{self.base_url}/auth/key"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get('credits', 0) > 0 or data.get('access', False)
                    return False
        except:
            return False
    
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        if not self.api_key:
            return "Error: No se ha configurado OPENROUTER_API_KEY"
        
        url = f"{self.base_url}/chat/completions"
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
                async with session.post(url, json=payload, headers=self.headers, timeout=self.timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data['choices'][0]['message']['content']
                    elif resp.status == 429:
                        return "Error: Rate limit excedido (OpenRouter). Espera un momento."
                    else:
                        error_text = await resp.text()
                        sanitized = sanitize_error(error_text)
                        return f"Error: OpenRouter respondió con {resp.status}: {sanitized}"
        except Exception as e:
            return f"Error: {e}"
