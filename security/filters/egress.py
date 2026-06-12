import re
import logging
from typing import Dict, Any

logger = logging.getLogger("ferdonan.firewall.egress")

class EgressFilter:
    def __init__(self, commands_blacklist_path: str, tools_blacklist_path: str):
        self.commands_blacklist = self._load_file(commands_blacklist_path)
        self.tools_blacklist = self._load_file(tools_blacklist_path)

    def _load_file(self, path: str) -> list:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except Exception as e:
            logger.error(f"Error cargando archivo de políticas Egress ({path}): {str(e)}")
            return []

    def _is_egress_enabled(self, route_config: Dict[str, Any]) -> bool:
        """
        Determina si el filtro egress está habilitado para esta ruta.
        Busca en:
        1. route_config.firewall.egress_filter_enabled (global)
        2. route_config.firewall.stages.*.egress_filter_enabled (cualquier stage)
        """
        # Verificar nivel global
        firewall = route_config.get("firewall", {})
        if firewall.get("egress_filter_enabled", False):
            return True
        
        # Verificar en stages
        stages = route_config.get("stages", [])
        for stage in stages:
            stage_firewall = stage.get("firewall", {})
            if stage_firewall.get("egress_filter_enabled", False):
                logger.info(f"Egress filter habilitado por stage: {stage.get('name', 'unknown')}")
                return True
        
        # Verificar en firewall.stages (formato antiguo anidado)
        stages_firewall = firewall.get("stages", {})
        for stage_name, stage_firewall_config in stages_firewall.items():
            if stage_firewall_config.get("egress_filter_enabled", False):
                logger.info(f"Egress filter habilitado por stage (formato antiguo): {stage_name}")
                return True
        
        return False

    def evaluate(self, output_content: str, route_config: Dict[str, Any]) -> bool:
        """
        Evaluación puramente determinista orientada al proceso.
        Activable por campo egress_filter_enabled en la ruta o en cualquier stage.
        """
        if not self._is_egress_enabled(route_config):
            return True

        # Validar comandos peligrosos en scripts o texto generado
        for cmd in self.commands_blacklist:
            if re.search(r'\b' + re.escape(cmd) + r'\b', output_content, re.IGNORECASE):
                logger.error(f"OUTPUT BLOQUEADO por Egress Filter. Comando prohibido detectado: {cmd}", extra={
                    "firewall_component": "egress",
                    "filter_layer": "layer1",
                    "trigger_pattern": cmd,
                    "action": "blocked"
                })
                return False

        # Validar uso de herramientas prohibidas en el output estructurado
        for tool in self.tools_blacklist:
            if tool in output_content:
                logger.error(f"OUTPUT BLOQUEADO por Egress Filter. Herramienta prohibida detectada: {tool}", extra={
                    "firewall_component": "egress",
                    "filter_layer": "layer1",
                    "trigger_pattern": tool,
                    "action": "blocked"
                })
                return False

        return True
