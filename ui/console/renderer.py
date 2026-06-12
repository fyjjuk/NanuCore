"""
Console renderer for FerdoNAN using ANSI codes and emojis.
Loads themes from YAML files.
"""

import os
import yaml
from typing import Optional, Dict, Any, List

class ConsoleRenderer:
    """Renderer for terminal output with theming support."""
    
    def __init__(self, theme_name: str = "refero", themes_dir: str = "ui/themes"):
        self.themes_dir = themes_dir
        self.theme = self._load_theme(theme_name)
        self.use_emoji = self.theme.get("console", {}).get("use_emoji", True)
        self.use_colors = self.theme.get("console", {}).get("use_colors", True)
    
    def _load_theme(self, theme_name: str) -> Dict[str, Any]:
        """Load theme from YAML file."""
        theme_path = os.path.join(self.themes_dir, f"{theme_name}.yaml")
        if not os.path.exists(theme_path):
            # Fallback to a basic theme
            return {
                "name": "basic",
                "colors": {},
                "badges": {},
                "console": {"use_emoji": True, "use_colors": True}
            }
        with open(theme_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _wrap_color(self, text: str, color_name: str) -> str:
        """Wrap text in ANSI color codes if colors enabled."""
        if not self.use_colors:
            return text
        colors = {
            "green": "\033[92m",
            "red": "\033[91m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "magenta": "\033[95m",
            "cyan": "\033[96m",
            "white": "\033[97m",
            "reset": "\033[0m",
        }
        color_code = colors.get(color_name, "")
        reset_code = colors.get("reset", "")
        return f"{color_code}{text}{reset_code}" if color_code else text
    
    def render_info(self, message: str, icon: str = "ℹ️", **kwargs) -> str:
        """Render info message."""
        prefix = f"{icon} " if self.use_emoji else "[INFO] "
        return f"{prefix}{message}"
    
    def render_success(self, message: str, icon: str = "✅", **kwargs) -> str:
        """Render success message."""
        prefix = f"{icon} " if self.use_emoji else "[OK] "
        colored = self._wrap_color(message, "green")
        return f"{prefix}{colored}"
    
    def render_error(self, message: str, icon: str = "❌", **kwargs) -> str:
        """Render error message."""
        prefix = f"{icon} " if self.use_emoji else "[ERROR] "
        colored = self._wrap_color(message, "red")
        return f"{prefix}{colored}"
    
    def render_warning(self, message: str, icon: str = "⚠️", **kwargs) -> str:
        """Render warning message."""
        prefix = f"{icon} " if self.use_emoji else "[WARN] "
        colored = self._wrap_color(message, "yellow")
        return f"{prefix}{colored}"
    
    def render_badge(self, text: str, style: str = "default", **kwargs) -> str:
        """Render a styled badge."""
        badges = self.theme.get("badges", {})
        badge = badges.get(style, f"[{text.upper()}]")
        if self.use_colors:
            # Apply color based on style
            color_map = {
                "info": "blue",
                "success": "green",
                "error": "red",
                "warning": "yellow",
                "gatekeeper": "magenta",
                "dnd": "cyan",
                "spotify": "green",
                "linux": "blue",
                "rag": "cyan",
            }
            color = color_map.get(style, "white")
            return self._wrap_color(badge, color)
        return badge
    
    def render_table(self, headers: List[str], rows: List[List[str]], **kwargs) -> str:
        """Render a simple table."""
        if not rows:
            return "No data"
        
        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Build header separator
        separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
        
        # Build header row
        header_row = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
        
        # Build data rows
        data_rows = []
        for row in rows:
            data_row = "| " + " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)) + " |"
            data_rows.append(data_row)
        
        lines = [separator, header_row, separator] + data_rows + [separator]
        return "\n".join(lines)
    
    def render_progress(self, current: int, total: int, width: int = 40, **kwargs) -> str:
        """Render a progress bar."""
        if total <= 0:
            return ""
        percent = current / total
        filled = int(width * percent)
        bar = "█" * filled + "░" * (width - filled)
        color = "green" if percent < 0.7 else "yellow" if percent < 0.9 else "red"
        colored_bar = self._wrap_color(bar, color)
        return f"[{colored_bar}] {percent*100:.1f}%"

    def render_prompt(self, message: str, **kwargs) -> str:
        """Render a user prompt."""
        return self.render_info(message, icon="🤔")

    # Integración con ASCII Studio
    def render_box(self, content: List[str], title: str = "", style: str = "single") -> str:
        """Renderiza contenido en una caja ASCII."""
        from ui.ascii.components import Box
        return Box.draw(title=title, content=content, style=style)
    
    def render_banner(self, style: str = "default") -> str:
        """Renderiza banner ASCII."""
        from ui.ascii.banners import Banners
        return Banners.get_banner(style)
    
    def render_table_ascii(self, headers: List[str], rows: List[List[str]]) -> str:
        """Renderiza tabla en formato ASCII."""
        from ui.ascii.components import Table
        return Table.draw(headers, rows)
    
    def render_startup_banner(self) -> None:
        """Muestra banner de inicio."""
        banner = self.render_banner("minimal")
        print(f"\n{banner}")
        print(self.render_info("Bienvenido a FerdoNAN v2.4.0"))
        print(self.render_info("Use /help para ver comandos disponibles\n"))
