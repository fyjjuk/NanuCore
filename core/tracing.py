import uuid
import contextvars

# Contexto global para propagar el ID de solicitud sin pasar argumentos extra
request_id_var = contextvars.ContextVar("request_id", default=None)

def generate_request_id():
    """Genera un nuevo UUID4 y lo establece en el contexto actual."""
    new_id = str(uuid.uuid4())
    request_id_var.set(new_id)
    return new_id

def get_request_id():
    """Recupera el request_id del contexto actual."""
    return request_id_var.get()
