"""Cargador de skills para NanuCore."""
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from nanu.core.interfaces import Tool
from nanu.core.tools.registry import ToolRegistry

class SkillLoader:
    def __init__(self):
        self.loaded_skills = set()  # Evitar cargar el mismo skill dos veces
    
    def load_skills_for_agent(self, agent_dir: Path) -> List[Tool]:
        """Carga skills desde nanu/skills/ y agents/<agent>/skills/"""
        tools = []
        global_skills_dir = Path("nanu/skills")
        agent_skills_dir = agent_dir / "skills"
        
        for skills_dir in [global_skills_dir, agent_skills_dir]:
            if not skills_dir.exists():
                continue
            for skill_dir in skills_dir.iterdir():
                if not skill_dir.is_dir():
                    continue
                skill_id = f"{skills_dir.name}/{skill_dir.name}"
                if skill_id in self.loaded_skills:
                    continue
                skill_tools = self._load_skill(skill_dir, agent_dir)
                if skill_tools:
                    tools.extend(skill_tools)
                    self.loaded_skills.add(skill_id)
        return tools
    
    def _load_skill(self, skill_dir: Path, agent_dir: Path) -> List[Tool]:
        """Carga un skill individual."""
        manifest = skill_dir / "skill.yaml"
        if not manifest.exists():
            print(f"⚠️ Skill sin manifest: {skill_dir}")
            return []
        
        import yaml
        with open(manifest, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        name = config.get('name', skill_dir.name)
        print(f"📦 Cargando skill: {name}")
        
        # Instalar dependencias si existen
        req_file = skill_dir / "requirements.txt"
        if req_file.exists():
            print(f"   📦 Instalando dependencias para {name}...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_file)], 
                           capture_output=True, text=True)
        
        # Buscar herramientas en tools/ del skill
        tools_dir = skill_dir / "tools"
        if not tools_dir.exists():
            return []
        
        tools = []
        for py_file in tools_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            # Importar dinámicamente
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Buscar clases que hereden de Tool
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Tool) and attr is not Tool:
                    tool_instance = attr()
                    # Evitar registrar si ya existe
                    if not ToolRegistry().get(tool_instance.name):
                        ToolRegistry().register(tool_instance)
                        tools.append(tool_instance)
                        print(f"   ✓ Herramienta registrada: {tool_instance.name}")
                    else:
                        print(f"   ⚠️ Herramienta ya registrada: {tool_instance.name}")
        return tools
