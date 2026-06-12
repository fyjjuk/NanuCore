import re
from typing import Optional
from core.logger import logger
from services.sanitizer.factory import create_sanitizer

class Sanitizer:
    def __init__(self, enabled: bool = True, model: Optional[str] = None, ):
        config = {
            "enabled": enabled,
            "use_llm": model is not None,
            "model": model
        }
        self._sanitizer = create_sanitizer(config)

    def clean(self, user_input: str) -> str:
        return self._sanitizer.clean(user_input)
