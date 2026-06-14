"""Cliente para Ollama."""
import aiohttp
from typing import Dict, Any
from .base import LLMClient

class OllamaClient(LLMClient):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get('host', 'http://localhost:11434')
    
    async def available(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.host}/api/tags", timeout=5) as resp:
                    return resp.status == 200
        except:
            return False
    
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get('temperature', self.temperature),
                "num_predict": kwargs.get('max_tokens', self.max_tokens)
            }
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=self.timeout) as resp:
                if resp.status != 200:
                    return f"Error: Ollama respondió con {resp.status}"
                data = await resp.json()
                return data.get('response', '')
