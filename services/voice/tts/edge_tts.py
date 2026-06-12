import subprocess
import tempfile
import os
import re
from services.voice.interfaces import BaseTTS

class EdgeTTS(BaseTTS):
    def __init__(self, default_voice: str = "es-ES-ElviraNeural"):
        self.default_voice = default_voice

    def _sanitize_text(self, text: str) -> str:
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 800:
            text = text[:800] + "..."
        return text

    def speak(self, text: str, voice_id: str = None) -> None:
        # Si voice_id es "es" o una cadena vacía, usar el valor por defecto
        if voice_id is None or voice_id == "es":
            voice = self.default_voice
        else:
            voice = voice_id
        clean_text = self._sanitize_text(text)
        if not clean_text:
            return
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            cmd = ["edge-tts", "--text", clean_text, "--voice", voice, "--write-media", tmp_path]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["mpg123", "-q", tmp_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            print(f"[TTS Error] {e}")
        finally:
            os.unlink(tmp_path)
