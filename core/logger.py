import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger

# Asegurar que el directorio logs existe
os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("ferdonan")
logger.setLevel(logging.INFO)

formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')

# Solo logging a archivo, no a consola
file_handler = RotatingFileHandler("logs/ferdonan.log", maxBytes=5*1024*1024, backupCount=5)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# No añadimos ningún StreamHandler a la consola
