from .base import LLMClient

class LocalClient(LLMClient):
    def generate_response(self, prompt, system_prompt, config) -> str:
        ti, to = 10, 20
        self._log_telemetry("local", "mock", ti, to)
        return f"[Mock] Respuesta de {self.agent_id}: {prompt[:50]}..."
