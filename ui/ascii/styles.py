"""
Estilos y decoradores ASCII.
"""

from functools import wraps
from typing import Callable


class Style:
    """Decoradores para estilizar output de funciones."""
    
    @staticmethod
    def boxed(title: str = "", style: str = "single"):
        """Decorador que envuelve output en una caja."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                from .components import Box
                result = func(*args, **kwargs)
                if isinstance(result, str):
                    lines = result.split('\n')
                    return Box.draw(title=title, content=lines, style=style)
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def with_spinner(message: str = "Procesando"):
        """Decorador que muestra spinner durante ejecución."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                from .components import Spinner
                spinner = Spinner(message)
                spinner.start()
                try:
                    result = func(*args, **kwargs)
                    spinner.stop(final_message=message)
                    return result
                except Exception as e:
                    spinner.stop(final_message=f"Error: {e}")
                    raise
            return wrapper
        return decorator
    
    @staticmethod
    def with_progress(total: int, description: str = "Progreso"):
        """Decorador que muestra barra de progreso."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                from .components import ProgressBar
                pb = ProgressBar(total)
                print(f"{description}:")
                
                # Modificar kwargs para pasar callback de progreso
                def update_progress(current):
                    print(f"\r{pb.update(current)}", end="")
                
                kwargs['progress_callback'] = update_progress
                result = func(*args, **kwargs)
                print()  # Nueva línea al final
                return result
            return wrapper
        return decorator
