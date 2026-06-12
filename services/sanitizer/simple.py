import re
from .base import BaseSanitizer

class SimpleSanitizer(BaseSanitizer):
    def clean(self, user_input: str) -> str:
        text = user_input.strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\x20-\x7EáéíóúñÑüÜ¿?¡!]', '', text)
        return text
