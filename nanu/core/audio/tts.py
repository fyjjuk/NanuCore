"""Text-to-Speech service con sanitización y capacidad de interrupción."""
import subprocess
import tempfile
import os
import threading
import time
import atexit
from .sanitizer import TTSSanitizer

class TTSService:
    _instance = None
    _current_process = None
    _current_lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._sanitizer = TTSSanitizer()
        # Asegurar que al salir se detenga cualquier reproducción
        atexit.register(self.stop)
    
    def stop(self):
        """Detiene la reproducción actual inmediatamente."""
        with self._current_lock:
            if self._current_process and self._current_process.poll() is None:
                try:
                    self._current_process.terminate()
                    self._current_process.wait(timeout=1)
                except:
                    pass
                finally:
                    self._current_process = None
    
    def speak(self, text: str, voice: str = "es-ES-ElviraNeural", async_mode: bool = True):
        """Sintetiza y reproduce texto, sanitizándolo previamente."""
        if not text or len(text.strip()) < 2:
            return
        
        # Sanitizar el texto antes de hablar
        clean_text = self._sanitizer.sanitize(text)
        if not clean_text:
            return
        
        # Si hay reproducción en curso, detenerla (para evitar solapamiento)
        self.stop()
        
        if async_mode:
            thread = threading.Thread(target=self._speak_sync, args=(clean_text, voice), daemon=True)
            thread.start()
        else:
            self._speak_sync(clean_text, voice)
    
    def _speak_sync(self, text: str, voice: str):
        """Ejecuta edge-tts y reproduce, almacenando el proceso actual."""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            path = f.name
        
        try:
            # Generar MP3
            subprocess.run(
                ["edge-tts", "--text", text, "--voice", voice, "--write-media", path],
                capture_output=True, timeout=30, check=True
            )
            # Reproducir con mpg123 y guardar proceso para poder detenerlo
            with self._current_lock:
                self._current_process = subprocess.Popen(
                    ["mpg123", "-q", path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            # Esperar a que termine la reproducción (si no se interrumpe)
            if self._current_process:
                self._current_process.wait()
                with self._current_lock:
                    if self._current_process and self._current_process.poll() is not None:
                        self._current_process = None
        except subprocess.CalledProcessError as e:
            print(f"TTS error: {e}")
        except Exception as e:
            print(f"TTS error: {e}")
        finally:
            os.unlink(path)
            # Asegurar que el proceso se limpie
            with self._current_lock:
                if self._current_process and self._current_process.poll() is not None:
                    self._current_process = None
