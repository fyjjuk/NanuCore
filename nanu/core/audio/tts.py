"""Text-to-Speech service con sanitización y capacidad de interrupción."""
import subprocess
import tempfile
import os
import threading
import time
import atexit
from .sanitizer import TTSSanitizer
from nanu.core.logging import get_logger

logger = get_logger(__name__)

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
        atexit.register(self.stop)
        logger.debug("TTSService inicializado")
    
    def stop(self):
        """Detiene la reproducción actual inmediatamente."""
        with self._current_lock:
            if self._current_process and self._current_process.poll() is None:
                try:
                    self._current_process.terminate()
                    self._current_process.wait(timeout=1)
                    logger.debug("Reproducción TTS detenida")
                except Exception as e:
                    logger.error(f"Error deteniendo TTS: {e}")
                finally:
                    self._current_process = None
    
    def speak(self, text: str, voice: str = "es-ES-ElviraNeural", async_mode: bool = True):
        """Sintetiza y reproduce texto, sanitizándolo previamente."""
        if not text or len(text.strip()) < 2:
            logger.debug("Texto vacío o demasiado corto para TTS")
            return
        
        clean_text = self._sanitizer.sanitize(text)
        if not clean_text:
            logger.debug("Texto vacío después de sanitización")
            return
        
        logger.debug(f"TTS: '{clean_text[:50]}...'")
        
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
            logger.debug(f"Generando TTS: {text[:30]}...")
            subprocess.run(
                ["edge-tts", "--text", text, "--voice", voice, "--write-media", path],
                capture_output=True, timeout=30, check=True
            )
            logger.debug(f"Reproduciendo: {path}")
            with self._current_lock:
                self._current_process = subprocess.Popen(
                    ["mpg123", "-q", path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            if self._current_process:
                self._current_process.wait()
                with self._current_lock:
                    if self._current_process and self._current_process.poll() is not None:
                        self._current_process = None
                        logger.debug("Reproducción TTS completada")
        except subprocess.CalledProcessError as e:
            logger.error(f"TTS error (edge-tts): {e}")
        except FileNotFoundError as e:
            logger.error(f"TTS error: {e}. ¿Está instalado edge-tts o mpg123?")
        except Exception as e:
            logger.error(f"TTS error: {e}")
        finally:
            try:
                os.unlink(path)
            except Exception as e:
                logger.error(f"Error eliminando archivo temporal: {e}")
            with self._current_lock:
                if self._current_process and self._current_process.poll() is not None:
                    self._current_process = None
