.PHONY: help install dev prod build up down logs restart clean test lint format

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install dependencies locally
	python -m venv venv
	.\venv\Scripts\activate.ps1; pip install -r requirements.txt
	.\venv\Scripts\activate.ps1; pip install -e .

install-dev: ## Install with development dependencies
	python -m venv venv
	.\venv\Scripts\activate.ps1; pip install -r requirements.txt
	.\venv\Scripts\activate.ps1; pip install -e .[dev]

# Environment setup
env: ## Copy example.env to .env
	copy example.env .env
	@echo "Please edit .env file with your configuration"

# Docker operations
build: ## Build Docker images
	docker-compose build

dev: ## Start development environment
	docker-compose up --build -d

prod: ## Start production environment
	docker-compose -f docker-compose.prod.yml up --build -d

up: ## Start services (development)
	docker-compose up -d

down: ## Stop all services
	docker-compose down
	docker-compose -f docker-compose.prod.yml down

logs: ## View logs
	docker-compose logs -f

restart: ## Restart services
	docker-compose restart

ps: ## Show running containers
	docker-compose ps

# Ollama operations
ollama-models: ## List Ollama models
	docker exec -it ollama ollama list

ollama-pull: ## Pull default Ollama model
	docker exec -it ollama ollama pull llama3.2:3b

ollama-pull-mistral: ## Pull Mistral model
	docker exec -it ollama ollama pull mistral:7b

# Maintenance
clean: ## Clean up Docker resources
	docker-compose down -v --rmi all
	docker system prune -f

clean-logs: ## Clean log files
	if exist logs (rmdir /s /q logs)
	mkdir logs

# Development
test: ## Run tests
	.\venv\Scripts\activate.ps1; pytest

lint: ## Run code linting
	.\venv\Scripts\activate.ps1; flake8 src/

format: ## Format code
	.\venv\Scripts\activate.ps1; black src/

# Monitoring
status: ## Check service status
	@echo "=== Docker Compose Status ==="
	docker-compose ps
	@echo ""
	@echo "=== Ollama Health ==="
	curl -f http://localhost:11434/api/tags 2>/dev/null && echo "✅ Ollama OK" || echo "❌ Ollama Error"
	@echo ""
	@echo "=== Container Resources ==="
	docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Backup
backup: ## Backup Ollama models and data
	docker run --rm -v llmtenderbot_ollama_data:/data -v ${PWD}/backup:/backup alpine tar czf /backup/ollama_backup_$(shell powershell -Command "Get-Date -Format 'yyyyMMdd_HHmmss'").tar.gz -C /data .

# Quick start
quick-start: env build dev ollama-pull ## Quick start (setup env, build, start, pull model)
	@echo "✅ Quick start completed!"
	@echo "Don't forget to edit .env file with your tokens!" 