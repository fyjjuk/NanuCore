"""Cliente para Hugging Face Inference API."""
import aiohttp
import os
from typing import Dict, Any, Optional
from .base import LLMClient

class HuggingFaceClient(LLMClient):
    """Cliente para Hugging Face Inference API."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key') or os.environ.get('HUGGINGFACE_API_KEY')
        self.base_url = config.get('base_url', 'https://api-inference.huggingface.co/models')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Los modelos de HF tienen nombres completos: "meta-llama/Llama-3.2-3B-Instruct"
        # Aseguramos que el modelo esté completo
        if self.model and not '/' in self.model:
            # Fallback para modelos comunes
            self.model = f"meta-llama/{self.model}" if "llama" in self.model.lower() else self.model
    
    async def available(self) -> bool:
        """Verifica si la API key es válida."""
        if not self.api_key:
            return False
        try:
            url = f"{self.base_url}/{self.model}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=5) as resp:
                    return resp.status != 403  # 403 significa key inválida
        except:
            return False
    
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Genera una respuesta usando Hugging Face."""
        if not self.api_key:
            return "Error: No se ha configurado HUGGINGFACE_API_KEY"
        
        # Hugging Face no soporta system_prompt de forma nativa en todas las APIs
        # Lo combinamos con el prompt
        final_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        url = f"{self.base_url}/{self.model}"
        payload = {
            "inputs": final_prompt,
            "parameters": {
                "temperature": kwargs.get('temperature', self.temperature),
                "max_new_tokens": kwargs.get('max_tokens', self.max_tokens),
                "return_full_text": False,
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=self.headers, timeout=self.timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # La respuesta puede ser un dict con "generated_text" o una lista
                        if isinstance(data, list) and len(data) > 0:
                            return data[0].get('generated_text', '')
                        elif isinstance(data, dict):
                            return data.get('generated_text', '')
                        else:
                            return str(data)
                    elif resp.status == 429:
                        return "Error: Rate limit excedido (Hugging Face). Espera un momento."
                    else:
                        error_text = await resp.text()
                        return f"Error: Hugging Face respondió con {resp.status}: {error_text[:100]}"
        except Exception as e:
            return f"Error: {e}"
