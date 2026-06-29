from pathlib import Path
import re
import yaml
from typing import Dict, Any, Optional, List
from difflib import SequenceMatcher
import unicodedata
from nanu.core.agent import Agent
from nanu.core.logging import get_logger

logger = get_logger(__name__)

# Stopwords en español (palabras muy comunes que no aportan significado)
STOPWORDS = {
    'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
    'de', 'en', 'por', 'para', 'con', 'sin', 'sobre', 'entre',
    'a', 'ante', 'bajo', 'cabe', 'contra', 'desde', 'durante',
    'hacia', 'hasta', 'mediante', 'según', 'tras', 'versus', 'vía',
    'que', 'quien', 'cual', 'cuyo', 'donde', 'cuando', 'como',
    'y', 'o', 'u', 'ni', 'pero', 'sino', 'aunque', 'porque',
    'si', 'entonces', 'pues', 'así', 'más', 'menos', 'muy',
    'yo', 'tú', 'él', 'ella', 'nosotros', 'vosotros', 'ellos',
    'me', 'te', 'se', 'le', 'lo', 'la', 'les', 'los', 'las'
}

def normalize_text(text: str) -> str:
    """
    Normaliza el texto: minúsculas, elimina acentos y caracteres especiales.
    """
    # Convertir a minúsculas
    text = text.lower()
    # Eliminar acentos
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    # Reemplazar caracteres especiales por espacios
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return text

def remove_stopwords(words: List[str]) -> List[str]:
    """Elimina stopwords de una lista de palabras."""
    return [w for w in words if w not in STOPWORDS and len(w) > 1]

def calculate_fuzzy_score(a: str, b: str) -> float:
    """Calcula la similitud difusa entre dos strings (0.0 - 1.0)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

class IntentRouter:
    def route(self, agent: Agent, user_input: str, threshold: float = 0.05) -> Optional[Dict[str, Any]]:
        user_lower = user_input.lower().strip()
        if not user_lower:
            return None
        
        # Normalizar input para coincidencia
        normalized_input = normalize_text(user_lower)
        input_words = normalized_input.split()
        input_words_no_stop = remove_stopwords(input_words)
        
        routes_dir = Path(agent.config_path).parent / "routes"
        if not routes_dir.exists():
            logger.debug(f"No hay directorio de rutas para {agent.id}")
            return None
        
        best_route = None
        best_score = 0.0
        
        for yaml_file in routes_dir.glob("*.yaml"):
            with open(yaml_file, 'r', encoding='utf-8') as f:
                route = yaml.safe_load(f)
                if not route or 'route_id' not in route:
                    continue
                
                desc = route.get('description', '').lower()
                if not desc:
                    continue
                
                # Normalizar descripción
                normalized_desc = normalize_text(desc)
                desc_words = normalized_desc.split()
                desc_words_no_stop = remove_stopwords(desc_words)
                
                if not desc_words_no_stop or not input_words_no_stop:
                    continue
                
                # 1. Coincidencia exacta de palabras (método original mejorado)
                # Palabras del input que están en la descripción
                matches = 0
                for word in input_words_no_stop:
                    if word in desc_words_no_stop:
                        matches += 1
                
                # Si hay coincidencias exactas, calcular score básico
                if matches > 0:
                    base_score = matches / max(len(desc_words_no_stop), 1)
                else:
                    base_score = 0.0
                
                # 2. Coincidencia difusa con frases completas (captura errores tipográficos)
                fuzzy_score = calculate_fuzzy_score(normalized_input, normalized_desc)
                
                # 3. Coincidencia de frases exactas (cuando el input contiene la descripción)
                phrase_score = 0.0
                if normalized_desc in normalized_input:
                    # Si la descripción completa está contenida, alta puntuación
                    phrase_score = 1.0
                elif normalized_desc in user_lower:
                    phrase_score = 0.8
                
                # Combinar scores con pesos
                # Peso: 40% coincidencia exacta, 30% fuzzy, 30% frase exacta
                combined_score = (0.4 * base_score) + (0.3 * fuzzy_score) + (0.3 * phrase_score)
                
                # Ajuste por longitud de palabras clave: si hay más palabras en la descripción,
                # es más específica, pero penalizar si el input es muy corto
                if len(desc_words_no_stop) > 5 and len(input_words_no_stop) < 3:
                    combined_score *= 0.8
                elif len(desc_words_no_stop) <= 2 and len(input_words_no_stop) >= 3:
                    combined_score *= 0.6
                
                # Si el input coincide exactamente con la descripción, score máximo
                if user_lower == desc or normalized_input == normalized_desc:
                    combined_score = 1.0
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_route = route
        
        # Verificar si la mejor puntuación supera el umbral
        if best_route and best_score >= threshold:
            logger.debug(f"Ruta seleccionada: {best_route['route_id']} (score={best_score:.3f})")
            return best_route
        
        # Fallback: buscar ruta "comando" si existe
        if user_lower and routes_dir.exists():
            for yaml_file in routes_dir.glob("*.yaml"):
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    route = yaml.safe_load(f)
                    if route and route.get('route_id') == 'comando':
                        logger.debug(f"Fallback a comando (input: '{user_lower}')")
                        return route
        
        logger.debug(f"No se encontró ruta para: '{user_input}'")
        return None
