"""Configuración global de pytest"""
import sys
import os

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
