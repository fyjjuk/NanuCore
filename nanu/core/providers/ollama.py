"""Cliente asíncrono para Ollama."""
import aiohttp
import json
from typing import AsyncIterator, Dict, Any
from nanu.core.interfaces import LLMClient

class OllamaClient(LLMClient):
    """Cliente para Ollama usando aiohttp."""
    
    def __init__(self, config: Dict[str, Any]):
        self.host = config.get('host', 'http://localhost:11434')
        self.model = config.get('model', 'phi3:mini')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 2048)
        self.timeout = config.get('timeout', 30)
    
    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        """Genera respuesta completa."""
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
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
    
    async def stream(self, prompt: str, system: str = "", **kwargs) -> AsyncIterator[str]:
        """Genera respuesta con streaming."""
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": True,
            "options": {
                "temperature": kwargs.get('temperature', self.temperature),
                "num_predict": kwargs.get('max_tokens', self.max_tokens)
            }
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=self.timeout) as resp:
                async for line in resp.content:
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            token = chunk.get('response', '')
                            if token:
                                yield token
                            if chunk.get('done'):
                                break
                        except:
                            pass
