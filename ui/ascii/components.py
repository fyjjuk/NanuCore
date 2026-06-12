"""
Componentes visuales ASCII para UI de consola.
"""

import time
import threading
from typing import List, Optional, Callable


class Box:
    """Caja decorativa para texto."""
    
    @staticmethod
    def draw(title: str = "", content: List[str] = None, 
             width: int = 60, style: str = "single") -> str:
        """
        Dibuja una caja con contenido.
        
        Args:
            title: Título de la caja
            content: Lista de líneas de contenido
            width: Ancho de la caja
            style: Estilo de borde ('single', 'double', 'rounded', 'bold')
        """
        styles = {
            "single": {"tl": "┌", "tr": "┐", "bl": "└", "br": "┘", "h": "─", "v": "│"},
            "double": {"tl": "╔", "tr": "╗", "bl": "╚", "br": "╝", "h": "═", "v": "║"},
            "rounded": {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"},
            "bold": {"tl": "┏", "tr": "┓", "bl": "┗", "br": "┛", "h": "━", "v": "┃"},
        }
        
        s = styles.get(style, styles["single"])
        lines = []
        
        # Borde superior
        top = f"{s['tl']}{s['h'] * (width - 2)}{s['tr']}"
        lines.append(top)
        
        # Título
        if title:
            title_line = f"{s['v']} {title:<{width-4}} {s['v']}"
            lines.append(title_line)
            lines.append(f"{s['v']}{s['h'] * (width - 2)}{s['v']}")
        
        # Contenido
        if content:
            for line in content:
                if len(line) > width - 4:
                    line = line[:width-7] + "..."
                padded = f"{s['v']} {line:<{width-4}} {s['v']}"
                lines.append(padded)
        
        # Borde inferior
        bottom = f"{s['bl']}{s['h'] * (width - 2)}{s['br']}"
        lines.append(bottom)
        
        return "\n".join(lines)
    
    @staticmethod
    def info(message: str) -> str:
        """Caja de información."""
        return Box.draw(content=[f"ℹ️  {message}"], style="rounded")
    
    @staticmethod
    def success(message: str) -> str:
        """Caja de éxito."""
        return Box.draw(content=[f"✅ {message}"], style="double")
    
    @staticmethod
    def error(message: str) -> str:
        """Caja de error."""
        return Box.draw(content=[f"❌ {message}"], style="bold")
    
    @staticmethod
    def warning(message: str) -> str:
        """Caja de advertencia."""
        return Box.draw(content=[f"⚠️  {message}"], style="rounded")


class ProgressBar:
    """Barra de progreso ASCII."""
    
    def __init__(self, total: int, width: int = 40, 
                 fill_char: str = "█", empty_char: str = "░"):
        self.total = total
        self.width = width
        self.fill_char = fill_char
        self.empty_char = empty_char
        self.current = 0
    
    def update(self, current: int) -> str:
        """Actualiza barra de progreso."""
        self.current = min(current, self.total)
        percent = self.current / self.total
        filled = int(self.width * percent)
        bar = self.fill_char * filled + self.empty_char * (self.width - filled)
        return f"[{bar}] {percent*100:.1f}%"
    
    def render(self) -> str:
        """Renderiza barra de progreso."""
        return self.update(self.current)


class Spinner:
    """Animación de spinner en consola."""
    
    def __init__(self, message: str = "Procesando", 
                 frames: List[str] = None, delay: float = 0.1):
        self.message = message
        self.frames = frames or ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.delay = delay
        self._running = False
        self._thread = None
    
    def _spin(self):
        """Hilo de spinner."""
        import sys
        idx = 0
        while self._running:
            frame = self.frames[idx % len(self.frames)]
            sys.stdout.write(f"\r{frame} {self.message}...")
            sys.stdout.flush()
            time.sleep(self.delay)
            idx += 1
    
    def start(self):
        """Inicia spinner en hilo separado."""
        self._running = True
        self._thread = threading.Thread(target=self._spin)
        self._thread.daemon = True
        self._thread.start()
    
    def stop(self, final_message: Optional[str] = None):
        """Detiene spinner."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
        import sys
        if final_message:
            sys.stdout.write(f"\r✅ {final_message}\n")
        else:
            sys.stdout.write("\r✓ Hecho.\n")
        sys.stdout.flush()


class Table:
    """Tabla ASCII formateada."""
    
    @staticmethod
    def draw(headers: List[str], rows: List[List[str]], 
             align: str = "left") -> str:
        """
        Dibuja una tabla ASCII.
        
        Args:
            headers: Lista de encabezados
            rows: Lista de filas (cada fila es lista de celdas)
            align: Alineación ('left', 'center', 'right')
        """
        if not rows:
            return "No hay datos"
        
        # Calcular anchos de columna
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Construir separador
        separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
        
        # Alineación
        align_map = {
            "left": lambda s, w: s.ljust(w),
            "center": lambda s, w: s.center(w),
            "right": lambda s, w: s.rjust(w),
        }
        align_func = align_map.get(align, align_map["left"])
        
        # Encabezados
        header_row = "| " + " | ".join(align_func(str(h), col_widths[i]) 
                                        for i, h in enumerate(headers)) + " |"
        
        # Filas
        data_rows = []
        for row in rows:
            data_row = "| " + " | ".join(
                align_func(str(cell), col_widths[i]) 
                for i, cell in enumerate(row[:len(headers)])
            ) + " |"
            data_rows.append(data_row)
        
        # Ensamblar tabla
        lines = [separator, header_row, separator] + data_rows + [separator]
        return "\n".join(lines)
