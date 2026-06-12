"""Menú de utilidades generado dinámicamente a partir de plugins."""
import os
import sys
from core.plugin.manager import PluginManager

# Colores ANSI
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"

def display_plugin_menu():
    """Muestra un menú interactivo con todos los plugins descubiertos."""
    manager = PluginManager()
    plugins = manager.get_all_plugins()
    
    if not plugins:
        print(f"{YELLOW}⚠️ No se encontraron utilidades.{RESET}")
        return
    
    categories = {}
    for plugin in plugins.values():
        cat = plugin.category
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(plugin)
    
    while True:
        print(f"\n{CYAN}{'='*60}{RESET}")
        print(f"{MAGENTA}🛠️  MENÚ DE UTILIDADES FERDONAN{RESET}")
        print(f"{CYAN}{'='*60}{RESET}")
        
        idx = 1
        plugin_map = {}
        
        # Iconos por categoría
        cat_icons = {
            "diagnostic": "🔍",
            "user": "👤",
            "shell": "🐚",
            "cli": "⚙️",
            "repomix": "📦"
        }
        
        for cat, cat_plugins in categories.items():
            icon = cat_icons.get(cat, "📁")
            print(f"\n  {icon} {cat.upper()} ─")
            for plugin in cat_plugins:
                print(f"     {idx:2}. {plugin.name}")
                print(f"        {plugin.description[:60]}")
                plugin_map[idx] = plugin
                idx += 1
        
        print(f"\n  🔄 0. Volver al selector de agentes")
        print(f"{CYAN}{'='*60}{RESET}")
        
        try:
            choice = input(f"\n{GREEN}👉 Elige una opción:{RESET} ").strip()
            if choice == "0":
                break
            idx = int(choice)
            if idx in plugin_map:
                print(f"\n{YELLOW}⏳ Ejecutando: {plugin_map[idx].name}{RESET}")
                print(f"{CYAN}{'─'*60}{RESET}")
                plugin_map[idx].run()
                print(f"{CYAN}{'─'*60}{RESET}")
                input(f"\n{GREEN}Presiona Enter para continuar...{RESET}")
            else:
                print(f"{YELLOW}❌ Opción inválida. Elige entre 1 y {len(plugin_map)}{RESET}")
        except ValueError:
            print(f"{YELLOW}❌ Por favor, ingresa un número válido{RESET}")
        except KeyboardInterrupt:
            print(f"\n{YELLOW}👋 Saliendo...{RESET}")
            break

if __name__ == "__main__":
    display_plugin_menu()
