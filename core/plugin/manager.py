"""Gestor de plugins para utilidades."""
import os
import importlib
import inspect
from typing import Dict, List, Type
from core.logger import logger
from .interface import UtilityPlugin

class PluginManager:
    """Descubre y carga plugins de utilidad desde el directorio utils/."""
    
    def __init__(self, utils_dir: str = "utils"):
        self.utils_dir = utils_dir
        self._plugins: Dict[str, UtilityPlugin] = {}
        self._discover_plugins()
    
    def _discover_plugins(self):
        """Recorre el directorio utils/ buscando módulos que contengan clases UtilityPlugin."""
        if not os.path.exists(self.utils_dir):
            logger.warning(f"Directorio de utilidades no encontrado: {self.utils_dir}")
            return
        
        for root, dirs, files in os.walk(self.utils_dir):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    module_path = os.path.join(root, file)
                    self._load_plugin_from_file(module_path)
    
    def _load_plugin_from_file(self, file_path: str):
        """Carga un plugin desde un archivo Python."""
        try:
            rel_path = os.path.relpath(file_path, start=os.path.dirname(self.utils_dir))
            module_name = rel_path.replace(os.sep, '.')[:-3]
            module = importlib.import_module(module_name)
            
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, UtilityPlugin) and obj is not UtilityPlugin):
                    plugin_instance = obj()
                    self._plugins[plugin_instance.name] = plugin_instance
                    logger.debug(f"Plugin cargado: {plugin_instance.name} ({plugin_instance.category})")
        except Exception as e:
            logger.error(f"Error cargando plugin {file_path}: {e}")
    
    def get_plugins_by_category(self, category: str) -> List[UtilityPlugin]:
        """Retorna lista de plugins de una categoría."""
        return [p for p in self._plugins.values() if p.category == category]
    
    def get_all_plugins(self) -> Dict[str, UtilityPlugin]:
        """Retorna todos los plugins."""
        return self._plugins.copy()
    
    def get_categories(self) -> List[str]:
        """Retorna lista de categorías únicas."""
        return list(set(p.category for p in self._plugins.values()))
    
    def run_plugin(self, name: str) -> bool:
        """Ejecuta un plugin por su nombre. Retorna True si existe y se ejecutó."""
        if name in self._plugins:
            self._plugins[name].run()
            return True
        return False
