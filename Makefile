.PHONY: help install run test dashboard clean backup logs health

# Colores para output (opcional)
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
NC     := \033[0m # No Color

help: ## Muestra esta ayuda
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Instala dependencias y prepara el entorno
	@echo "$(YELLOW)🔧 Creando entorno virtual...$(NC)"
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	@echo "$(GREEN)✅ Dependencias instaladas.$(NC)"
	@echo "   Activa el entorno con: source venv/bin/activate"

run: ## Ejecuta el asistente principal
	@echo "$(YELLOW)🚀 Iniciando FerdoNAN...$(NC)"
	python main.py

dashboard: ## Inicia el dashboard web (puerto 8000)
	@echo "$(YELLOW)📊 Iniciando dashboard...$(NC)"
	python web/dashboard.py

test: ## Ejecuta los tests unitarios
	@echo "$(YELLOW)🧪 Ejecutando tests...$(NC)"
	pytest tests/ -v

clean: ## Limpia archivos temporales y cachés
	@echo "$(YELLOW)🧹 Limpiando archivos temporales...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf logs/*.log
	@echo "$(GREEN)✅ Limpieza completada.$(NC)"

backup: ## Crea un backup del proyecto
	@echo "$(YELLOW)💾 Creando backup...$(NC)"
	python scripts/user/backup_cli.py crear

logs: ## Muestra los logs en tiempo real
	@echo "$(YELLOW)📜 Mostrando logs...$(NC)"
	python scripts/user/logs_tail.py

health: ## Health check del sistema
	@echo "$(YELLOW)🩺 Health check...$(NC)"
	python scripts/diagnostic/check_health.py
