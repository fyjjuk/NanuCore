"""
Streaming - Manejo de respuestas en tiempo real
"""

import logging
import time

logger = logging.getLogger(__name__)


class StreamHandler:
    """Responsable de manejar streaming de respuestas de LLM"""
    
    @staticmethod
    def stream_with_yield(llm, prompt: str, system_prompt: str, llm_config: dict):
        """
        Ejecuta streaming y hace yield de tokens (para salida en tiempo real)
        """
        if hasattr(llm, 'stream_response'):
            logger.info("Usando streaming nativo del LLM")
            for token in llm.stream_response(prompt, system_prompt, llm_config):
                yield token
                time.sleep(0.01)  # Pequeña pausa para evitar saturar
        else:
            logger.warning(f"LLM no soporta streaming, usando generate_response")
            yield llm.generate_response(prompt, system_prompt, llm_config)
    
    @staticmethod
    def stream_response_legacy(llm, prompt: str, system_prompt: str, llm_config: dict) -> str:
        """
        Método legacy para compatibilidad: retorna la respuesta completa
        """
        response = ""
        for token in StreamHandler.stream_with_yield(llm, prompt, system_prompt, llm_config):
            response += token
        return response
