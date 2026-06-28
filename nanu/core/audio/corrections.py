"""Sistema de correcciones fonéticas para STT."""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from nanu.core.logging import get_logger

logger = get_logger(__name__)

class PhoneticCorrector:
    """Corrige interpretaciones erróneas del STT basado en un diccionario."""
    
    _instance = None
    _corrections_file = "data/corrections/phonetic_map.json"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance
    
    def _load(self):
        """Carga el diccionario de correcciones desde archivo."""
        self.corrections: Dict[str, str] = {}
        self.reverse_map: Dict[str, str] = {}
        
        corrections_path = Path(self._corrections_file)
        if corrections_path.exists():
            try:
                with open(corrections_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.corrections = data.get('corrections', {})
                    # Construir mapa inverso
                    for correct, variants in self.corrections.items():
                        if isinstance(variants, list):
                            for variant in variants:
                                self.reverse_map[variant.lower()] = correct
                        elif isinstance(variants, str):
                            self.reverse_map[variants.lower()] = correct
                logger.debug(f"Correcciones cargadas: {len(self.corrections)} entradas")
            except Exception as e:
                logger.error(f"Error cargando correcciones: {e}")
    
    def save(self):
        """Guarda el diccionario de correcciones."""
        corrections_path = Path(self._corrections_file)
        corrections_path.parent.mkdir(parents=True, exist_ok=True)
        # Convertir reverse_map a formato de almacenamiento
        store_corrections = {}
        for correct, variants in self.corrections.items():
            if isinstance(variants, list):
                store_corrections[correct] = variants
            else:
                store_corrections[correct] = [variants]
        with open(corrections_path, 'w', encoding='utf-8') as f:
            json.dump({"corrections": store_corrections}, f, ensure_ascii=False, indent=2)
        logger.debug("Correcciones guardadas")
    
    def correct(self, text: str) -> str:
        """Aplica correcciones al texto (soporta frases completas)."""
        if not text:
            return text
        
        text_lower = text.lower()
        result = text
        
        # Ordenar variantes por longitud (las más largas primero)
        sorted_variants = sorted(self.reverse_map.items(), key=lambda x: len(x[0]), reverse=True)
        
        for variant, correct in sorted_variants:
            if variant in text_lower:
                # Reemplazo simple (no usa límites de palabra para frases con espacios)
                pattern = re.compile(re.escape(variant), re.IGNORECASE)
                result = pattern.sub(correct, result)
        
        if result != text:
            logger.debug(f"Corrección aplicada: '{text}' → '{result}'")
        return result
    
    def add_correction(self, wrong: str, correct: str):
        """Añade una nueva corrección."""
        wrong_lower = wrong.lower()
        correct_lower = correct.lower()
        
        # Buscar si ya existe la corrección para este correct
        if correct_lower in self.corrections:
            existing = self.corrections[correct_lower]
            if isinstance(existing, list):
                if wrong_lower not in [v.lower() for v in existing]:
                    existing.append(wrong)
            else:
                self.corrections[correct_lower] = [existing, wrong]
        else:
            self.corrections[correct_lower] = [wrong]
        
        # Actualizar reverse_map
        self.reverse_map[wrong_lower] = correct_lower
        self.save()
        logger.info(f"Corrección guardada: '{wrong}' → '{correct}'")
    
    def list_corrections(self) -> str:
        """Lista todas las correcciones guardadas."""
        if not self.corrections:
            return "No hay correcciones guardadas."
        lines = ["📋 Correcciones fonéticas:"]
        for correct, variants in self.corrections.items():
            if isinstance(variants, list):
                for v in variants:
                    lines.append(f"  '{v}' → '{correct}'")
            else:
                lines.append(f"  '{variants}' → '{correct}'")
        return "\n".join(lines)

# Instancia global
corrector = PhoneticCorrector()
