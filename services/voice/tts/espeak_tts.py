import subprocess
from services.voice.interfaces import BaseTTS

class EspeakTTS(BaseTTS):
    def __init__(self, default_voice: str = "es", speed: int = 160, pitch: int = 60):
        self.default_voice = default_voice
        self.speed = speed
        self.pitch = pitch

    def speak(self, text: str, voice_id: str = None) -> None:
        lang = voice_id or self.default_voice
        voice = "es-mb-es1" if lang.startswith('es') else "en-us"
        cmd = ["espeak-ng", "-v", voice, "-s", str(self.speed), "-p", str(self.pitch), text]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    tts = EspeakTTS(speed=180, pitch=65)
    tts.speak("Prueba de velocidad y tono mejorado", "es")
