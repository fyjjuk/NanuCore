"""
Demo de componentes ASCII Studio.
"""

from .banners import Banners
from .components import Box, Table, Spinner
from .styles import Style


def run_demo():
    """Ejecuta demo de ASCII Studio."""
    print("\n" + "=" * 60)
    print("ASCII Studio Demo")
    print("=" * 60 + "\n")
    
    # Banners
    print("1. Banners:")
    print(Banners.get_banner("minimal"))
    print()
    
    # Cajas
    print("2. Boxes:")
    print(Box.info("Este es un mensaje informativo"))
    print()
    print(Box.success("Operación completada exitosamente"))
    print()
    print(Box.warning("Precaución: Esto es una advertencia"))
    print()
    print(Box.error("Error crítico en el sistema"))
    print()
    
    # Tabla
    print("3. Table:")
    table = Table.draw(
        headers=["ID", "Nombre", "Estado"],
        rows=[
            ["1", "Agente D&D", "Activo"],
            ["2", "Spotify Player", "Activo"],
            ["3", "Buscador Web", "Inactivo"],
        ]
    )
    print(table)
    print()
    
    # Spinner demo
    print("4. Spinner (3 segundos):")
    spinner = Spinner("Cargando datos", delay=0.05)
    spinner.start()
    import time
    time.sleep(3)
    spinner.stop("Datos cargados exitosamente")
    print()
    
    print("=" * 60)
    print("Demo completada!")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
