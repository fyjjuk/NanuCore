"""
Internationalization (i18n) module for FerdoNAN.
Loads message dictionaries from JSON files.
"""

import json
import os
from typing import Dict, Any, Optional
from functools import lru_cache


class Localization:
    """Cargador de diccionarios de mensajes por idioma."""
    
    _instances: Dict[str, 'Localization'] = {}
    _default_locale: str = "en"
    
    def __init__(self, locale: str = "en", locales_dir: str = "locales"):
        self.locale = locale
        self.locales_dir = locales_dir
        self.messages = self._load_messages()
    
    @classmethod
    def get_instance(cls, locale: Optional[str] = None) -> 'Localization':
        """Obtiene o crea una instancia singleton por idioma."""
        locale = locale or cls._default_locale
        if locale not in cls._instances:
            cls._instances[locale] = cls(locale)
        return cls._instances[locale]
    
    @classmethod
    def set_default_locale(cls, locale: str):
        """Establece el idioma por defecto."""
        cls._default_locale = locale
    
    def _load_messages(self) -> Dict[str, Any]:
        """Carga el diccionario de mensajes desde archivo JSON."""
        file_path = os.path.join(self.locales_dir, self.locale, "messages.json")
        
        if not os.path.exists(file_path):
            # Fallback a inglés si el archivo no existe
            fallback_path = os.path.join(self.locales_dir, "en", "messages.json")
            if os.path.exists(fallback_path):
                with open(fallback_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get(self, key: str, **kwargs) -> str:
        """
        Obtiene un mensaje por su clave (formato: 'category.key').
        Ejemplo: get('errors.ingress_blocked')
        """
        parts = key.split('.')
        value = self.messages
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part, {})
            else:
                break
        
        if isinstance(value, str):
            return value.format(**kwargs) if kwargs else value
        
        # Si no se encuentra, devolver la clave
        return key
    
    def get_error(self, error_key: str, **kwargs) -> str:
        """Obtiene un mensaje de error."""
        return self.get(f"errors.{error_key}", **kwargs)
    
    def get_info(self, info_key: str, **kwargs) -> str:
        """Obtiene un mensaje informativo."""
        return self.get(f"info.{info_key}", **kwargs)
    
    def get_prompt(self, prompt_key: str, **kwargs) -> str:
        """Obtiene un mensaje de prompt."""
        return self.get(f"prompts.{prompt_key}", **kwargs)


# Función de conveniencia para acceder rápidamente
_loc = Localization.get_instance()

def t(key: str, **kwargs) -> str:
    """Función de traducción rápida."""
    return _loc.get(key, **kwargs)


__all__ = ['Localization', 't', 'set_default_locale']
