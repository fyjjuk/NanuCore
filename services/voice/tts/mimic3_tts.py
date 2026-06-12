import subprocess
import tempfile
import os
from services.voice.interfaces import BaseTTS

class Mimic3TTS(BaseTTS):
    def __init__(self, default_voice: str = "es_ES", speed: float = 1.0):
        self.default_voice = default_voice
        self.speed = speed

    def speak(self, text: str, voice_id: str = None) -> None:
        voice = voice_id or self.default_voice
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            # Generar WAV con mimic3
            cmd = [
                'mimic3',
                '--voice', voice,
                '--length-scale', str(self.speed),
                '--output', tmp_path,
                text
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Reproducir con aplay
            subprocess.run(['aplay', '-q', tmp_path], check=True)
        finally:
            os.unlink(tmp_path)

if __name__ == "__main__":
    tts = Mimic3TTS()
    tts.speak("Hola, esta es una prueba de Mimic3.", "es_ES")
