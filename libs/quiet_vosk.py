import os
import sys
import warnings
import contextlib

# Forzar nivel de log de Vosk a -1
os.environ["VOSK_LOG_LEVEL"] = "-1"
os.environ["GLOG_minloglevel"] = "2"  # Para posibles logs de Google

# Redirigir stderr a null durante la importación y el uso
stderr_fileno = sys.stderr.fileno()
devnull_fd = os.open(os.devnull, os.O_WRONLY)

def silence_vosk():
    """Redirige stderr a /dev/null para silenciar Vosk."""
    os.dup2(devnull_fd, stderr_fileno)

def unsilence_vosk():
    """Restaura stderr original (si se necesita)."""
    # No implementado porque no se necesita
    pass

# Aplicar silencio inmediatamente
silence_vosk()

# Re-importar vosk después de silenciar (si ya se importó, forzar recarga)
import importlib
if 'vosk' in sys.modules:
    importlib.reload(sys.modules['vosk'])
else:
    import vosk
