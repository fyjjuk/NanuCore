from abc import ABC, abstractmethod

class BaseSTT(ABC):
    @abstractmethod
    def transcribe(self, audio_data: bytes) -> str:
        """Transcribe audio a texto."""
        pass

class BaseTTS(ABC):
    @abstractmethod
    def speak(self, text: str, voice_id: str = None) -> None:
        """Sintetiza y reproduce el texto."""
        pass
