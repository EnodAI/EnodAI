.PHONY: help build up down restart logs test clean deploy backup restore

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Variables
DOCKER_COMPOSE := docker-compose
DOCKER_COMPOSE_PROD := docker-compose -f docker-compose.yml -f docker-compose.prod.yml
PROJECT_NAME := enodai

help: ## Show this help message
	@echo "$(GREEN)KamAlertAI - Makefile Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

## Development Commands

build: ## Build all Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) build

up: ## Start all services
	@echo "$(GREEN)Starting services...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Services started$(NC)"
	@echo "Collector:   http://localhost:8080"
	@echo "AI Service:  http://localhost:8082"
	@echo "Grafana:     http://localhost:3000 (admin/kam_password)"
	@echo "Prometheus:  http://localhost:9090"

down: ## Stop all services
	@echo "$(YELLOW)Stopping services...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ Services stopped$(NC)"

restart: down up ## Restart all services

logs: ## Show logs from all services
	$(DOCKER_COMPOSE) logs -f

logs-collector: ## Show logs from collector service
	$(DOCKER_COMPOSE) logs -f collector

logs-ai: ## Show logs from AI service
	$(DOCKER_COMPOSE) logs -f ai-service

ps: ## Show running containers
	$(DOCKER_COMPOSE) ps

## Testing Commands

test: test-ai test-collector ## Run all tests

test-ai: ## Run AI service tests
	@echo "$(GREEN)Running AI service tests...$(NC)"
	cd ai-service && pytest -v --cov=app --cov-report=term-missing

test-collector: ## Run collector service tests
	@echo "$(GREEN)Running collector service tests...$(NC)"
	cd collector && go test -v -cover ./...

test-watch: ## Run tests in watch mode
	cd ai-service && pytest-watch

lint: lint-ai lint-collector ## Run all linters

lint-ai: ## Lint Python code
	@echo "$(GREEN)Linting Python code...$(NC)"
	cd ai-service && black --check app tests
	cd ai-service && flake8 app tests
	cd ai-service && mypy app

lint-fix: ## Fix linting issues
	@echo "$(GREEN)Fixing Python code style...$(NC)"
	cd ai-service && black app tests
	cd ai-service && isort app tests

lint-collector: ## Lint Go code
	@echo "$(GREEN)Linting Go code...$(NC)"
	cd collector && go fmt ./...
	cd collector && go vet ./...
	cd collector && golint ./...

## Database Commands

db-shell: ## Connect to PostgreSQL shell
	docker exec -it $(PROJECT_NAME)-postgresql-1 psql -U kam_user -d kam_alerts

db-backup: ## Backup database
	@echo "$(GREEN)Backing up database...$(NC)"
	./scripts/backup.sh

db-restore: ## Restore database
	@echo "$(YELLOW)Restoring database...$(NC)"
	./scripts/restore.sh

db-migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	# Add migration commands here

## Deployment Commands

deploy-dev: build up ## Deploy development environment
	@echo "$(GREEN)Development environment deployed$(NC)"

deploy-prod: ## Deploy production environment
	@echo "$(GREEN)Deploying production environment...$(NC)"
	$(DOCKER_COMPOSE_PROD) up -d --build
	@echo "$(GREEN)✅ Production deployed$(NC)"

## Utility Commands

clean: ## Clean up Docker resources
	@echo "$(YELLOW)Cleaning up Docker resources...$(NC)"
	$(DOCKER_COMPOSE) down -v --remove-orphans
	docker system prune -f
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

clean-all: clean ## Clean everything including volumes
	@echo "$(RED)⚠️  This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker volume rm $(PROJECT_NAME)_postgres_data $(PROJECT_NAME)_redis_data $(PROJECT_NAME)_ollama_data $(PROJECT_NAME)_prometheus_data $(PROJECT_NAME)_grafana_data 2>/dev/null || true; \
		echo "$(GREEN)✅ All volumes deleted$(NC)"; \
	fi

setup-ollama: ## Download Ollama models
	@echo "$(GREEN)Downloading Ollama models...$(NC)"
	docker exec $(PROJECT_NAME)-ollama-1 ollama pull llama2
	@echo "$(GREEN)✅ Ollama models downloaded$(NC)"

health-check: ## Check health of all services
	@echo "$(GREEN)Checking service health...$(NC)"
	@echo -n "Collector:   "; curl -s http://localhost:8080/health | jq -r '.status' || echo "$(RED)DOWN$(NC)"
	@echo -n "AI Service:  "; curl -s http://localhost:8082/health | jq -r '.status' || echo "$(RED)DOWN$(NC)"
	@echo -n "Prometheus:  "; curl -s http://localhost:9090/-/healthy && echo "$(GREEN)UP$(NC)" || echo "$(RED)DOWN$(NC)"
	@echo -n "Grafana:     "; curl -s http://localhost:3000/api/health | jq -r '.database' || echo "$(RED)DOWN$(NC)"

send-test-data: ## Send test data to services
	@echo "$(GREEN)Sending test data...$(NC)"
	./test_data.sh

install-deps: install-deps-ai install-deps-collector ## Install all dependencies

install-deps-ai: ## Install Python dependencies
	@echo "$(GREEN)Installing Python dependencies...$(NC)"
	cd ai-service && pip install -r requirements.txt

install-deps-collector: ## Install Go dependencies
	@echo "$(GREEN)Installing Go dependencies...$(NC)"
	cd collector && go mod download

## Monitoring Commands

prometheus: ## Open Prometheus UI
	@echo "Opening Prometheus..."
	@open http://localhost:9090 || xdg-open http://localhost:9090

grafana: ## Open Grafana UI
	@echo "Opening Grafana..."
	@open http://localhost:3000 || xdg-open http://localhost:3000

api-docs: ## Open API documentation
	@echo "Opening API docs..."
	@open http://localhost:8082/docs || xdg-open http://localhost:8082/docs

## Development Tools

shell-ai: ## Open shell in AI service container
	docker exec -it $(PROJECT_NAME)-ai-service-1 /bin/bash

shell-collector: ## Open shell in collector container
	docker exec -it $(PROJECT_NAME)-collector-1 /bin/sh

shell-db: ## Open shell in PostgreSQL container
	docker exec -it $(PROJECT_NAME)-postgresql-1 /bin/bash

redis-cli: ## Open Redis CLI
	docker exec -it $(PROJECT_NAME)-redis-1 redis-cli

## Performance Commands

bench: bench-collector ## Run benchmarks

bench-collector: ## Run collector benchmarks
	@echo "$(GREEN)Running collector benchmarks...$(NC)"
	cd collector && go test -bench=. -benchmem

load-test: ## Run load tests
	@echo "$(GREEN)Running load tests...$(NC)"
	./scripts/load_test.sh

## Documentation Commands

docs-build: ## Build documentation
	@echo "$(GREEN)Building documentation...$(NC)"
	# Add documentation build commands

docs-serve: ## Serve documentation locally
	@echo "$(GREEN)Serving documentation...$(NC)"
	# Add documentation serve commands

## CI/CD Commands

ci-test: ## Run CI tests
	@echo "$(GREEN)Running CI tests...$(NC)"
	$(MAKE) test
	$(MAKE) lint

ci-build: ## Build for CI
	@echo "$(GREEN)Building for CI...$(NC)"
	$(MAKE) build

## Quick Start

quickstart: build up setup-ollama send-test-data ## Quick start everything
	@echo ""
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)  KamAlertAI is ready!$(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo ""
	@echo "Access points:"
	@echo "  • Grafana:     http://localhost:3000"
	@echo "  • API Docs:    http://localhost:8082/docs"
	@echo "  • Prometheus:  http://localhost:9090"
	@echo ""
	@echo "Next steps:"
	@echo "  • View logs:   make logs"
	@echo "  • Run tests:   make test"
	@echo "  • Health check: make health-check"
	@echo ""
