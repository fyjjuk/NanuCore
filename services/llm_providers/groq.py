from groq import Groq
from .base import LLMClient

class GroqClient(LLMClient):
    def generate_response(self, prompt, system_prompt, config) -> str:
        client = Groq(api_key=self.api_key)
        model_name = config.get("model", "llama3-8b-8192")
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model=model_name,
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 2048)
        )
        self._log_telemetry("groq", model_name,
                            chat_completion.usage.prompt_tokens,
                            chat_completion.usage.completion_tokens)
        return chat_completion.choices[0].message.content
