"""Gemini LLM provider using google-genai (v2 API)."""

from .base import LLMClient

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("Warning: google-genai not installed. Gemini client will not work.")


class GeminiClient(LLMClient):
    """Cliente para Gemini API usando la nueva biblioteca google-genai."""
    
    def generate_response(self, prompt: str, system_prompt: str, config: dict) -> str:
        if not GENAI_AVAILABLE:
            raise ImportError("google-genai library is required for Gemini client. "
                            "Install with: pip install google-genai")
        
        # Configurar el cliente
        client = genai.Client(api_key=self.api_key)
        
        model_name = config.get("model", "gemini-1.5-flash")
        
        # Configurar los parámetros de generación
        generation_config = types.GenerateContentConfig(
            temperature=config.get("temperature", 0.7),
            max_output_tokens=config.get("max_tokens", 2048),
            system_instruction=system_prompt if system_prompt else None,
        )
        
        # Generar respuesta
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=generation_config,
        )
        
        # Registrar telemetría (la nueva API puede no tener usage_metadata)
        try:
            if hasattr(response, 'usage_metadata'):
                self._log_telemetry(
                    "gemini", model_name,
                    response.usage_metadata.prompt_token_count or 0,
                    response.usage_metadata.candidates_token_count or 0
                )
        except Exception:
            pass  # Telemetría opcional
        
        return response.text
    
    def stream_response(self, prompt: str, system_prompt: str = "", config: dict = None):
        """
        Genera respuesta con streaming usando Gemini.
        
        Yields:
            str: Tokens generados en tiempo real
        """
        if not GENAI_AVAILABLE:
            raise ImportError("google-genai library is required for Gemini client.")
        
        if config is None:
            config = {}
        
        client = genai.Client(api_key=self.api_key)
        model_name = config.get("model", "gemini-1.5-flash")
        
        generation_config = types.GenerateContentConfig(
            temperature=config.get("temperature", 0.7),
            max_output_tokens=config.get("max_tokens", 2048),
            system_instruction=system_prompt if system_prompt else None,
        )
        
        # Streaming
        response = client.models.generate_content_stream(
            model=model_name,
            contents=prompt,
            config=generation_config,
        )
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
