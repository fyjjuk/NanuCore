"""Cliente para Google Gemini con soporte para múltiples API keys y cooldown."""
import asyncio
import aiohttp
import os
import time
from typing import Dict, Any, Optional, List
from .base import LLMClient
from nanu.core.utils.sanitize import sanitize_error
from nanu.core.logging import get_logger

logger = get_logger(__name__)


class GeminiClient(LLMClient):
    """Cliente para Gemini con rotación inteligente de claves y cooldown."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_keys = self._load_api_keys()
        self.current_key_index = 0
        # Cooldown por clave: índice -> timestamp de expiración
        self._key_cooldowns: Dict[int, float] = {}
        self._cooldown_seconds = 60  # Cooldown por defecto para claves que fallan
        self._last_key_used: Optional[int] = None
    
    def _load_api_keys(self) -> List[str]:
        """
        Carga múltiples API keys de variables de entorno.
        Soporta GOOGLE_API_KEY_1, GOOGLE_API_KEY_2, ... y GOOGLE_API_KEY
        """
        keys = []
        
        # Buscar GOOGLE_API_KEY_1, GOOGLE_API_KEY_2, etc.
        for key_name, value in os.environ.items():
            if key_name.startswith('GOOGLE_API_KEY_') and key_name != 'GOOGLE_API_KEY':
                if value and value.strip():
                    keys.append(value.strip())
                    logger.debug(f"Cargada API key desde {key_name}")
        
        # Si no se encontraron keys con sufijo, usar GOOGLE_API_KEY
        if not keys:
            single_key = os.environ.get('GOOGLE_API_KEY')
            if single_key and single_key.strip():
                keys.append(single_key.strip())
                logger.debug("Cargada API key desde GOOGLE_API_KEY")
        else:
            # También añadir GOOGLE_API_KEY como respaldo si no está ya en la lista
            single_key = os.environ.get('GOOGLE_API_KEY')
            if single_key and single_key.strip() and single_key not in keys:
                keys.append(single_key.strip())
                logger.debug("Cargada API key adicional desde GOOGLE_API_KEY")
        
        if keys:
            logger.info(f"Cargadas {len(keys)} API keys de Gemini")
        else:
            logger.warning("No se encontraron API keys de Gemini")
        
        return keys
    
    def _get_current_key(self) -> Optional[str]:
        """Obtiene la clave actual, respetando cooldowns."""
        if not self.api_keys:
            return None
        
        # Buscar una clave que no esté en cooldown
        for i in range(len(self.api_keys)):
            idx = (self.current_key_index + i) % len(self.api_keys)
            if idx not in self._key_cooldowns or time.time() > self._key_cooldowns[idx]:
                self.current_key_index = idx
                self._last_key_used = idx
                return self.api_keys[idx]
        
        # Si todas las claves están en cooldown, esperar
        min_cooldown = min(self._key_cooldowns.values())
        wait_time = max(0, min_cooldown - time.time())
        if wait_time > 0:
            logger.warning(f"Todas las claves en cooldown. Esperando {wait_time:.1f}s...")
            # Devolver la primera clave y esperar que el caller maneje el error
            # O podemos implementar un sleep aquí, pero mejor manejarlo en el caller
            return self.api_keys[self.current_key_index % len(self.api_keys)]
        return None
    
    def _mark_key_failed(self, key_idx: int, retry_after: int = 60):
        """Marca una clave como fallida y la pone en cooldown."""
        self._key_cooldowns[key_idx] = time.time() + retry_after
        logger.warning(f"Gemini key {key_idx + 1} en cooldown por {retry_after}s")
    
    def _rotate_key(self):
        """Rota a la siguiente clave disponible."""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.debug(f"Rotando a Gemini key {self.current_key_index + 1}/{len(self.api_keys)}")
    
    async def available(self) -> bool:
        """Verifica si hay al menos una clave disponible (no en cooldown)."""
        if not self.api_keys:
            return False
        # Verificar si alguna clave no está en cooldown
        for i in range(len(self.api_keys)):
            if i not in self._key_cooldowns or time.time() > self._key_cooldowns[i]:
                return True
        return False
    
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """
        Genera una respuesta usando Gemini con rotación de claves y cooldown.
        """
        if not self.api_keys:
            return "Error: No hay API keys de Gemini configuradas"
        
        max_retries = len(self.api_keys) * 2  # Intentos adicionales para cooldowns
        last_error = None
        
        for attempt in range(max_retries):
            # Obtener clave disponible
            api_key = self._get_current_key()
            if not api_key:
                # Si no hay clave disponible, esperar un poco y reintentar
                logger.warning("No hay claves de Gemini disponibles, esperando...")
                await asyncio.sleep(5)
                continue
            
            # Obtener índice de la clave actual para marcarla si falla
            current_idx = self.current_key_index
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={api_key}"
            
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
                                text = data['candidates'][0]['content']['parts'][0]['text']
                                # Resetear cooldown en éxito
                                if current_idx in self._key_cooldowns:
                                    del self._key_cooldowns[current_idx]
                                return text
                            except (KeyError, IndexError) as e:
                                logger.error(f"Respuesta inesperada de Gemini: {e}")
                                return "Error: Respuesta inesperada de Gemini"
                        elif resp.status == 429:
                            # Rate limit - poner clave en cooldown
                            logger.warning(f"Rate limit en Gemini key {current_idx + 1}")
                            self._mark_key_failed(current_idx, 60)
                            self._rotate_key()
                            continue
                        elif resp.status == 403:
                            # API key inválida o sin permisos
                            logger.warning(f"Gemini key {current_idx + 1} inválida (403)")
                            self._mark_key_failed(current_idx, 300)  # Cooldown más largo
                            self._rotate_key()
                            continue
                        else:
                            error_text = await resp.text()
                            sanitized = sanitize_error(error_text)
                            # Si el error indica clave inválida, marcar en cooldown
                            if "API key not valid" in error_text or "invalid" in error_text.lower():
                                self._mark_key_failed(current_idx, 300)
                                self._rotate_key()
                                continue
                            return f"Error: Gemini respondió con {resp.status}: {sanitized}"
            except aiohttp.ClientError as e:
                logger.error(f"Error de conexión con Gemini: {e}")
                self._mark_key_failed(current_idx, 30)
                self._rotate_key()
                continue
            except asyncio.TimeoutError:
                logger.error(f"Timeout con Gemini (key {current_idx + 1})")
                self._mark_key_failed(current_idx, 30)
                self._rotate_key()
                continue
            except Exception as e:
                logger.error(f"Error inesperado con Gemini: {e}")
                self._mark_key_failed(current_idx, 60)
                self._rotate_key()
                continue
        
        return f"Error después de {max_retries} intentos: {last_error or 'Todas las claves fallaron'}"
    
    def get_key_status(self) -> List[Dict[str, Any]]:
        """Retorna el estado de todas las claves de Gemini."""
        status = []
        for i, key in enumerate(self.api_keys):
            is_cooldown = i in self._key_cooldowns
            cooldown_until = self._key_cooldowns.get(i, 0)
            remaining = max(0, cooldown_until - time.time()) if is_cooldown else 0
            status.append({
                "index": i + 1,
                "available": not is_cooldown,
                "cooldown_remaining": round(remaining, 1),
                "key_preview": key[:8] + "..." + key[-4:] if len(key) > 12 else key,
            })
        return status
