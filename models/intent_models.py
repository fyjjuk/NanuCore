"""Modelos de validación para rutas de agentes."""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

class StageConfig(BaseModel):
    """Configuración de un stage individual."""
    name: str
    provider: Literal["ollama", "gemini", "groq", "local"] = "ollama"
    model: Optional[str] = None
    prompt: str
    system_prompt: Optional[str] = ""
    output_key: str = "output"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=32768)
    timeout: int = Field(default=30, ge=5, le=300)
    api_key: Optional[str] = None
    
    @field_validator('model')
    def validate_model(cls, v, info):
        provider = info.data.get('provider', 'ollama')
        if provider == 'ollama' and v and not v.startswith(('llama', 'phi', 'qwen', 'mistral')):
            # No bloqueamos, solo advertimos (por si hay modelos personalizados)
            pass
        return v if v else None

class FirewallConfig(BaseModel):
    """Configuración de firewall por ruta."""
    egress_filter_enabled: bool = False
    semantic_output_filter_enabled: bool = False
    ingress_override: Optional[Dict[str, Any]] = None

class RouteModel(BaseModel):
    """Modelo validado para rutas de agentes."""
    route_id: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-z_][a-z0-9_]*$')
    type: Literal["cognitive", "script"] = "cognitive"
    description: str = Field(..., min_length=3, max_length=200)
    
    # Campos para rutas cognitivas
    system_prompt: Optional[str] = None
    stages: Optional[List[StageConfig]] = None
    final_output_key: Optional[str] = None
    stream: bool = False
    tools_allowed: Optional[List[str]] = None
    
    # Campos para rutas script
    script_path: Optional[str] = None
    script_args: Optional[Dict[str, Any]] = None
    
    # Firewall y seguridad
    gatekeeper_required: bool = False
    firewall: FirewallConfig = Field(default_factory=FirewallConfig)
    
    # Override de modelo
    override_config: Optional[Dict[str, Any]] = None
    
    @field_validator('stages')
    def validate_stages_consistency(cls, v, info):
        if v and info.data.get('type') != 'cognitive':
            raise ValueError('Solo rutas cognitivas pueden tener stages')
        if v and len(v) > 5:
            raise ValueError('Máximo 5 stages por ruta')
        return v if v else None
    
    @field_validator('script_path', mode='before')
    def validate_script_path(cls, v, info):
        """Validar script_path para rutas tipo script."""
        if info.data.get('type') == 'script' and not v:
            raise ValueError('Ruta tipo script requiere script_path')
        return v if v else None
    
    @field_validator('route_id', mode='before')
    def validate_route_id(cls, v, info):
        """Validar formato de route_id."""
        if ' ' in v:
            raise ValueError('route_id no puede contener espacios')
        return v.lower()
    
    model_config = ConfigDict(extra='forbid')

def validate_route(intent: Dict[str, Any]) -> tuple[bool, Optional[RouteModel], List[str]]:
    """
    Valida una ruta y retorna (es_valido, modelo, lista_errores).
    """
    errors = []
    try:
        model = RouteModel(**intent)
        return True, model, []
    except Exception as e:
        errors.append(str(e))
        return False, None, errors

def validate_routes_batch(routes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Valida múltiples rutas y retorna estadísticas.
    """
    valid_routes = []
    invalid_routes = []
    
    for route in routes:
        is_valid, model, errors = validate_route(route)
        if is_valid:
            valid_routes.append((route['route_id'], model))
        else:
            invalid_routes.append({
                'route_id': route.get('route_id', 'unknown'),
                'errors': errors,
                'original': route
            })
    
    return {
        'total': len(routes),
        'valid': len(valid_routes),
        'invalid': len(invalid_routes),
        'valid_routes': valid_routes,
        'invalid_routes': invalid_routes
    }
