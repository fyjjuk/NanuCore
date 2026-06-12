from typing import Dict, Any
from .base import BaseSanitizer
from .simple import SimpleSanitizer
from .llm import LLMSanitizer

def create_sanitizer(config: Dict[str, Any]) -> BaseSanitizer:
    enabled = config.get("enabled", True)
    if not enabled:
        # Sanitizador nulo: devuelve el input sin cambios
        class NullSanitizer(BaseSanitizer):
            def clean(self, user_input: str) -> str:
                return user_input
        return NullSanitizer()
    use_llm = config.get("use_llm", False)
    if use_llm:
        model = config.get("model", "phi3:mini")
        return LLMSanitizer(model=model)
    else:
        return SimpleSanitizer()
