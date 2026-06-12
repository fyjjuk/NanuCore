import psutil
import logging
import subprocess
import re
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("ferdonan.scheduler")

class ResourceScheduler:
    """
    Gestor de recursos para modos exclusive/parallel.
    Integra detección de VRAM (NVIDIA/AMD) y RAM.
    """
    
    def __init__(self, vram_threshold: float = 0.85):
        self.vram_threshold = vram_threshold
        self._vram_total_mb = self._detect_vram_total()
        
    def _detect_vram_total(self) -> Optional[int]:
        """Detecta VRAM total en MB usando nvidia-smi o rocm-smi."""
        try:
            # NVIDIA
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return int(result.stdout.strip().split('\n')[0])
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            # AMD
            result = subprocess.run(
                ["rocm-smi", "--showmeminfo", "vram"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                match = re.search(r'Total\s+VRAM\s+:\s+(\d+)', result.stdout)
                if match:
                    return int(match.group(1))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        logger.warning("No se pudo detectar VRAM. Usando solo RAM para scheduler.")
        return None
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Devuelve métricas actuales del sistema."""
        metrics = {
            "ram_percent": psutil.virtual_memory().percent,
            "ram_available_mb": psutil.virtual_memory().available / (1024 * 1024),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
        }
        
        if self._vram_total_mb:
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    vram_used_mb = int(result.stdout.strip().split('\n')[0])
                    metrics["vram_percent"] = (vram_used_mb / self._vram_total_mb) * 100
                    metrics["vram_used_mb"] = vram_used_mb
                    metrics["vram_total_mb"] = self._vram_total_mb
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        return metrics
    
    def can_run_parallel(self, agent) -> Tuple[bool, str]:
        """
        Determina si el agente puede ejecutarse en modo parallel.
        Retorna (bool, razón) para logging.
        """
        if agent.execution_mode != "parallel":
            return False, f"Modo del agente: {agent.execution_mode}"
        
        metrics = self.get_system_metrics()
        ram_ok = metrics["ram_percent"] < (self.vram_threshold * 100)
        
        reason = f"RAM: {metrics['ram_percent']:.1f}%"
        
        if "vram_percent" in metrics:
            vram_ok = metrics["vram_percent"] < (self.vram_threshold * 100)
            reason += f", VRAM: {metrics['vram_percent']:.1f}%"
            if not vram_ok:
                return False, f"{reason} (VRAM excede umbral)"
        
        if not ram_ok:
            return False, f"{reason} (RAM excede umbral)"
        
        return True, reason
    
    def suggest_degradation(self, agent_id: str) -> str:
        """Sugiere acción de degradación cuando parallel no es posible."""
        logger.warning(
            f"CONCURRENCY_MODE_CHANGE: Agente {agent_id} degradado a exclusive.",
            extra={"component": "scheduler", "action": "degradation"}
        )
        return "exclusive"
    def select_resource_profile(self, llm_provider_dict) -> str:
        """
        Determina el perfil de recursos ('high', 'medium', 'low') basado en recursos disponibles.
        Si el agente no tiene dynamic_resource_management activado, retorna 'default'.
        
        Umbrales configurables en config.settings:
          HIGH:   VRAM > 4000MB & RAM > 8000MB
          MEDIUM: VRAM > 2000MB & RAM > 4000MB
          LOW:    Fallback (dispositivos con poca memoria)
        """
        dynamic = llm_provider_dict.get("dynamic_resource_management", False)
        if not dynamic:
            return "default"
        
        metrics = self.get_system_metrics()
        ram_free_mb = metrics.get("ram_available_mb", 0)
        cpu_percent = metrics.get("cpu_percent", 0)
        
        # Detectar VRAM libre si está disponible
        vram_free_mb = None
        if "vram_total_mb" in metrics and "vram_used_mb" in metrics:
            vram_free_mb = metrics["vram_total_mb"] - metrics["vram_used_mb"]
        
        # Configuración de umbrales
        high_vram_threshold = 4000   # MB
        high_ram_threshold = 8000    # MB
        medium_vram_threshold = 2000 # MB
        medium_ram_threshold = 4000  # MB
        cpu_threshold = 70           # %
        
        # Lógica de selección mejorada
        profile = "low"
        reason = "Recursos limitados (fallback)"
        
        # Evitar modelo pesado si CPU está muy ocupado
        if cpu_percent > cpu_threshold:
            logger.warning(f"CPU muy ocupado ({cpu_percent:.1f}%). Seleccionando perfil LOW.")
            return "low"
        
        # Seleccionar basado en VRAM si disponible
        if vram_free_mb:
            if vram_free_mb > high_vram_threshold and ram_free_mb > high_ram_threshold:
                profile = "high"
                reason = f"VRAM={vram_free_mb:.0f}MB, RAM={ram_free_mb:.0f}MB (suficiente)"
            elif vram_free_mb > medium_vram_threshold and ram_free_mb > medium_ram_threshold:
                profile = "medium"
                reason = f"VRAM={vram_free_mb:.0f}MB, RAM={ram_free_mb:.0f}MB (moderado)"
            else:
                profile = "low"
                reason = f"VRAM={vram_free_mb:.0f}MB, RAM={ram_free_mb:.0f}MB (limitado)"
        else:
            # Fallback: usar solo RAM
            if ram_free_mb > high_ram_threshold:
                profile = "high"
                reason = f"RAM={ram_free_mb:.0f}MB (sin VRAM, pero suficiente)"
            elif ram_free_mb > medium_ram_threshold:
                profile = "medium"
                reason = f"RAM={ram_free_mb:.0f}MB (sin VRAM)"
            else:
                profile = "low"
                reason = f"RAM={ram_free_mb:.0f}MB (muy limitado)"
        
        logger.info(f"RESOURCE_PROFILE_SELECTION: {profile} ({reason})")
        return profile
