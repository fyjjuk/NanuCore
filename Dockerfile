FROM python:3.14-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para algunas librerías
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer puerto del dashboard (si se usa)
EXPOSE 8000

# Comando por defecto (se puede sobreescribir en docker-compose)
CMD ["python", "main.py"]
