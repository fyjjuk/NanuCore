"""Sanitizador de texto para TTS."""
import re

class TTSSanitizer:
    """Elimina emojis, formatos y caracteres no pronunciables."""
    
    # Patrón para emojis y otros caracteres no deseados
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # símbolos y pictogramas
        "\U0001F680-\U0001F6FF"  # transporte y mapas
        "\U0001F700-\U0001F77F"  # alquimia
        "\U0001F780-\U0001F7FF"  # geometría
        "\U0001F800-\U0001F8FF"  # flechas suplementarias
        "\U0001F900-\U0001F9FF"  # símbolos suplementarios
        "\U0001FA00-\U0001FA6F"  # símbolos de ajedrez
        "\U0001FA70-\U0001FAFF"  # símbolos variados
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251" 
        "]+", 
        flags=re.UNICODE
    )
    
    # URLs
    URL_PATTERN = re.compile(r'https?://\S+|www\.\S+')
    
    # Etiquetas HTML/XML
    HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
    
    @classmethod
    def sanitize(cls, text: str) -> str:
        """Limpia el texto eliminando emojis, URLs, etiquetas, y normaliza espacios."""
        if not text:
            return ""
        # Eliminar emojis
        text = cls.EMOJI_PATTERN.sub('', text)
        # Eliminar URLs
        text = cls.URL_PATTERN.sub('', text)
        # Eliminar etiquetas HTML
        text = cls.HTML_TAG_PATTERN.sub('', text)
        # Eliminar caracteres no imprimibles o de control (excepto saltos de línea)
        text = re.sub(r'[^\x20-\x7E\u00E0-\u00FC\u00F1\u00E7\u00A1\u00BF]', ' ', text)
        # Normalizar espacios múltiples y trim
        text = re.sub(r'\s+', ' ', text).strip()
        # Limitar longitud para evitar mensajes excesivamente largos
        if len(text) > 400:
            text = text[:397] + "..."
        return text
