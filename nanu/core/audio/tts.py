"""Text-to-Speech service - Edge TTS."""
import subprocess
import tempfile
import os
import threading

class TTSService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def speak(self, text: str, voice: str = "es-ES-ElviraNeural"):
        if not text or len(text.strip()) < 2:
            return
        thread = threading.Thread(target=self._speak, args=(text[:500], voice))
        thread.daemon = True
        thread.start()
    
    def _speak(self, text: str, voice: str):
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            path = f.name
        try:
            subprocess.run(
                ["edge-tts", "--text", text, "--voice", voice, "--write-media", path],
                capture_output=True, timeout=30
            )
            subprocess.run(["mpg123", "-q", path], capture_output=True, timeout=30)
        except Exception as e:
            print(f"TTS error: {e}")
        finally:
            os.unlink(path)
