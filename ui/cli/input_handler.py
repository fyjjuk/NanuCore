"""
Manejador de input con historial, autocompletado y comandos.
"""

import sys
import readline
from typing import Optional, Callable, List


class InputHandler:
    """Manejador de entrada de usuario con características avanzadas."""
    
    def __init__(self, completer: Optional[Callable] = None):
        self.history_file = ".ferdonan_input_history"
        self._setup_readline(completer)
        self._load_history()
    
    def _setup_readline(self, completer: Optional[Callable] = None):
        """Configura readline para historial y autocompletado."""
        try:
            if completer:
                readline.set_completer(completer)
                readline.parse_and_bind("tab: complete")
            
            readline.set_history_length(1000)
        except Exception:
            pass  # En Windows o entornos sin readline
    
    def _load_history(self):
        """Carga historial desde archivo."""
        try:
            readline.read_history_file(self.history_file)
        except (FileNotFoundError, OSError):
            pass
    
    def _save_history(self):
        """Guarda historial a archivo."""
        try:
            readline.write_history_file(self.history_file)
        except Exception:
            pass
    
    def prompt(self, prompt_text: str = "> ") -> str:
        """
        Muestra prompt y retorna input del usuario.
        
        Args:
            prompt_text: Texto del prompt
            
        Returns:
            str: Input del usuario (sin trailing newline)
        """
        try:
            user_input = input(prompt_text)
            if user_input and not user_input.startswith('/'):
                self._save_history()
            return user_input
        except EOFError:
            return "/exit"
        except KeyboardInterrupt:
            print()
            return "/exit"
    
    def add_to_history(self, line: str):
        """Añade línea al historial."""
        try:
            readline.add_history(line)
        except Exception:
            pass


class Completer:
    """Autocompletador para comandos CLI."""
    
    def __init__(self, command_registry):
        self.registry = command_registry
        self.matches = []
    
    def complete(self, text, state):
        """Método de autocompletado para readline."""
        if state == 0:
            # Iniciar nueva búsqueda
            if text.startswith('/'):
                self.matches = self.registry.suggest(text)
            else:
                self.matches = []
        
        try:
            return self.matches[state]
        except IndexError:
            return None
