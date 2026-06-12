import sys
import os

class StderrFilter:
    """Filtra mensajes de stderr que contengan ciertos patrones."""
    def __init__(self, original_stderr, exclude_patterns):
        self.original_stderr = original_stderr
        self.exclude_patterns = exclude_patterns

    def write(self, message):
        if not any(p in message for p in self.exclude_patterns):
            self.original_stderr.write(message)

    def flush(self):
        self.original_stderr.flush()

# Si no estamos en modo debug, activamos el filtro
if not os.environ.get("FERDONAN_DEBUG"):
    sys.stderr = StderrFilter(sys.stderr, ["LOG (VoskAPI)", "VoskAPI:"])
