# ============================================================================
# WhatsApp AI Support Agent - Makefile
# ============================================================================
# Project: WhatsApp Jira Integration Bot
# Author: Rahul
# License: MIT
# Version: 2.0.0
# ============================================================================

# ============================================================================
# CONFIGURATION VARIABLES
# ============================================================================

# Project settings
PROJECT_NAME := whatsapp-bot
PYTHON := python3
PIP := pip3
VENV := venv
PYTHON_VERSION := 3.9

# Application settings
APP_MODULE := main:app
HOST := 0.0.0.0
PORT := 8000
WORKERS := 4
RELOAD := --reload

# Docker settings
DOCKER_IMAGE := whatsapp-bot
DOCKER_TAG := latest
DOCKER_REGISTRY := your-registry.com
DOCKER_COMPOSE := docker-compose

# AWS settings
AWS_REGION := us-east-1
AWS_BUCKET := whatsapp-support-logs
AWS_PROFILE := default

# Testing settings
PYTEST := pytest
PYTEST_ARGS := -v --cov=. --cov-report=html --cov-report=term
TEST_PATH := tests/

# Linting settings
BLACK := black
ISORT := isort
FLAKE8 := flake8
MYPY := mypy
PYLINT := pylint

# Directories
SRC_DIR := .
SERVICES_DIR := services
ROUTES_DIR := routes
CONFIG_DIR := config
MODELS_DIR := models
UTILS_DIR := utils
LOGS_DIR := logs
DOCS_DIR := docs

# Files
REQUIREMENTS := requirements.txt
REQUIREMENTS_DEV := requirements-dev.txt
ENV_FILE := .env
ENV_EXAMPLE := .env.example

# Colors for output
COLOR_RESET := \033[0m
COLOR_BOLD := \033[1m
COLOR_GREEN := \033[32m
COLOR_YELLOW := \033[33m
COLOR_BLUE := \033[34m
COLOR_RED := \033[31m

# ============================================================================
# PHONY TARGETS (not actual files)
# ============================================================================

.PHONY: help install install-dev setup clean clean-pyc clean-build \
        run run-prod dev test test-coverage lint format check \
        docker-build docker-run docker-push docker-clean \
        deploy deploy-aws deploy-heroku \
        logs backup restore \
        db-migrate db-reset \
        docs docs-serve \
        ngrok webhook-test \
        security audit \
        all

# ============================================================================
# DEFAULT TARGET
# ============================================================================

.DEFAULT_GOAL := help

# ============================================================================
# HELP & DOCUMENTATION
# ============================================================================

help: ## 📚 Show this help message
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)"
	@echo "╔═══════════════════════════════════════════════════════════════╗"
	@echo "║        WhatsApp AI Support Agent - Makefile Commands        ║"
	@echo "╚═══════════════════════════════════════════════════════════════╝"
	@echo "$(COLOR_RESET)"
	@echo "$(COLOR_GREEN)📦 SETUP & INSTALLATION:$(COLOR_RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /setup|install|clean/ {printf "  $(COLOR_YELLOW)%-20s$(COLOR_RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(COLOR_GREEN)🚀 DEVELOPMENT:$(COLOR_RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /run|dev|test|lint|format/ {printf "  $(COLOR_YELLOW)%-20s$(COLOR_RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(COLOR_GREEN)🐳 DOCKER:$(COLOR_RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /docker/ {printf "  $(COLOR_YELLOW)%-20s$(COLOR_RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(COLOR_GREEN)☁️  DEPLOYMENT:$(COLOR_RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /deploy|backup|restore/ {printf "  $(COLOR_YELLOW)%-20s$(COLOR_RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(COLOR_GREEN)🔧 UTILITIES:$(COLOR_RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /logs|docs|ngrok|webhook|security|audit/ {printf "  $(COLOR_YELLOW)%-20s$(COLOR_RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(COLOR_BLUE)Usage: make [target]$(COLOR_RESET)"
	@echo ""

# ============================================================================
# SETUP & INSTALLATION
# ============================================================================

setup: ## 🔧 Complete project setup (venv + dependencies + .env)
	@echo "$(COLOR_GREEN)🚀 Setting up WhatsApp Bot project...$(COLOR_RESET)"
	@make install
	@make env-setup
	@make create-dirs
	@echo "$(COLOR_GREEN)✅ Setup complete! Run 'make run' to start.$(COLOR_RESET)"

install: ## 📦 Create virtual environment and install dependencies
	@echo "$(COLOR_BLUE)📦 Creating virtual environment...$(COLOR_RESET)"
	@$(PYTHON) -m venv $(VENV)
	@echo "$(COLOR_BLUE)📥 Installing dependencies...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && $(PIP) install --upgrade pip
	@. $(VENV)/bin/activate && $(PIP) install -r $(REQUIREMENTS)
	@echo "$(COLOR_GREEN)✅ Dependencies installed successfully!$(COLOR_RESET)"

install-dev: install ## 📦 Install development dependencies (testing, linting)
	@echo "$(COLOR_BLUE)📥 Installing development dependencies...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && $(PIP) install -r $(REQUIREMENTS_DEV)
	@. $(VENV)/bin/activate && $(PIP) install pre-commit
	@. $(VENV)/bin/activate && pre-commit install
	@echo "$(COLOR_GREEN)✅ Dev dependencies installed!$(COLOR_RESET)"

env-setup: ## 🔐 Create .env file from example
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "$(COLOR_YELLOW)📝 Creating .env file from template...$(COLOR_RESET)"; \
		cp $(ENV_EXAMPLE) $(ENV_FILE); \
		echo "$(COLOR_GREEN)✅ .env file created! Please update with your credentials.$(COLOR_RESET)"; \
	else \
		echo "$(COLOR_YELLOW)⚠️  .env file already exists. Skipping...$(COLOR_RESET)"; \
	fi

create-dirs: ## 📁 Create necessary project directories
	@echo "$(COLOR_BLUE)📁 Creating project directories...$(COLOR_RESET)"
	@mkdir -p $(LOGS_DIR)
	@mkdir -p $(DOCS_DIR)
	@mkdir -p tests/unit
	@mkdir -p tests/integration
	@mkdir -p data/backups
	@mkdir -p data/exports
	@echo "$(COLOR_GREEN)✅ Directories created!$(COLOR_RESET)"

# ============================================================================
# DEPENDENCY MANAGEMENT
# ============================================================================

freeze: ## 🧊 Freeze current dependencies to requirements.txt
	@echo "$(COLOR_BLUE)🧊 Freezing dependencies...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && $(PIP) freeze > $(REQUIREMENTS)
	@echo "$(COLOR_GREEN)✅ Dependencies frozen to $(REQUIREMENTS)$(COLOR_RESET)"

upgrade: ## ⬆️  Upgrade all dependencies to latest versions
	@echo "$(COLOR_YELLOW)⬆️  Upgrading all dependencies...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && $(PIP) list --outdated
	@. $(VENV)/bin/activate && $(PIP) install --upgrade -r $(REQUIREMENTS)
	@make freeze
	@echo "$(COLOR_GREEN)✅ Dependencies upgraded!$(COLOR_RESET)"

check-deps: ## 🔍 Check for security vulnerabilities in dependencies
	@echo "$(COLOR_BLUE)🔍 Checking dependencies for vulnerabilities...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && pip-audit
	@echo "$(COLOR_GREEN)✅ Dependency check complete!$(COLOR_RESET)"

# ============================================================================
# DEVELOPMENT
# ============================================================================

run: ## 🚀 Run the application (development mode with auto-reload)
	@echo "$(COLOR_GREEN)🚀 Starting WhatsApp Bot (Development Mode)...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && uvicorn $(APP_MODULE) $(RELOAD) --host $(HOST) --port $(PORT)

run-prod: ## 🏭 Run the application (production mode)
	@echo "$(COLOR_GREEN)🏭 Starting WhatsApp Bot (Production Mode)...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && gunicorn $(APP_MODULE) \
		-w $(WORKERS) \
		-k uvicorn.workers.UvicornWorker \
		--bind $(HOST):$(PORT) \
		--access-logfile $(LOGS_DIR)/access.log \
		--error-logfile $(LOGS_DIR)/error.log \
		--log-level info

dev: ## 💻 Start development environment (app + ngrok)
	@echo "$(COLOR_GREEN)💻 Starting development environment...$(COLOR_RESET)"
	@make -j2 run ngrok

stop: ## 🛑 Stop all running processes
	@echo "$(COLOR_RED)🛑 Stopping all processes...$(COLOR_RESET)"
	@pkill -f "uvicorn $(APP_MODULE)" || true
	@pkill -f "ngrok" || true
	@echo "$(COLOR_GREEN)✅ All processes stopped!$(COLOR_RESET)"

restart: stop run ## 🔄 Restart the application

# ============================================================================
# TESTING
# ============================================================================

test: ## 🧪 Run all tests
	@echo "$(COLOR_BLUE)🧪 Running tests...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_PATH) -v

test-coverage: ## 📊 Run tests with coverage report
	@echo "$(COLOR_BLUE)📊 Running tests with coverage...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && $(PYTEST) $(PYTEST_ARGS)
	@echo "$(COLOR_GREEN)✅ Coverage report generated in htmlcov/index.html$(COLOR_RESET)"

test-unit: ## 🔬 Run unit tests only
	@echo "$(COLOR_BLUE)🔬 Running unit tests...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && $(PYTEST) tests/unit/ -v

test-integration: ## 🔗 Run integration tests only
	@echo "$(COLOR_BLUE)🔗 Running integration tests...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && $(PYTEST) tests/integration/ -v

test-watch: ## 👀 Run tests in watch mode (re-run on file changes)
	@echo "$(COLOR_BLUE)👀 Running tests in watch mode...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && $(PYTEST) -f $(TEST_PATH)

# ============================================================================
# CODE QUALITY
# ============================================================================

lint: ## 🔍 Run all linters (flake8, pylint, mypy)
	@echo "$(COLOR_BLUE)🔍 Running linters...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && $(FLAKE8) $(SRC_DIR) --max-line-length=100 --exclude=$(VENV)
	@. $(VENV)/bin/activate && $(PYLINT) $(SERVICES_DIR) $(ROUTES_DIR) $(CONFIG_DIR) || true
	@. $(VENV)/bin/activate && $(MYPY) $(SRC_DIR) --ignore-missing-imports || true
	@echo "$(COLOR_GREEN)✅ Linting complete!$(COLOR_RESET)"

format: ## ✨ Auto-format code with black and isort
	@echo "$(COLOR_BLUE)✨ Formatting code...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && $(BLACK) $(SRC_DIR) --line-length=100 --exclude=$(VENV)
	@. $(VENV)/bin/activate && $(ISORT) $(SRC_DIR) --profile black
	@echo "$(COLOR_GREEN)✅ Code formatted!$(COLOR_RESET)"

check: lint test ## ✅ Run all checks (lint + test)
	@echo "$(COLOR_GREEN)✅ All checks passed!$(COLOR_RESET)"

# ============================================================================
# CLEANING
# ============================================================================

clean: clean-pyc clean-build clean-test ## 🧹 Clean all generated files

clean-pyc: ## 🗑️  Remove Python cache files
	@echo "$(COLOR_BLUE)🗑️  Removing Python cache files...$(COLOR_RESET)"
	@find . -type f -name '*.pyc' -delete
	@find . -type f -name '*.pyo' -delete
	@find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	@echo "$(COLOR_GREEN)✅ Python cache cleaned!$(COLOR_RESET)"

clean-build: ## 🗑️  Remove build artifacts
	@echo "$(COLOR_BLUE)🗑️  Removing build artifacts...$(COLOR_RESET)"
	@rm -rf build/
	@rm -rf dist/
	@rm -rf .eggs/
	@rm -rf *.egg-info
	@echo "$(COLOR_GREEN)✅ Build artifacts removed!$(COLOR_RESET)"

clean-test: ## 🗑️  Remove test and coverage artifacts
	@echo "$(COLOR_BLUE)🗑️  Removing test artifacts...$(COLOR_RESET)"
	@rm -rf .pytest_cache
	@rm -rf .coverage
	@rm -rf htmlcov/
	@rm -rf .mypy_cache
	@echo "$(COLOR_GREEN)✅ Test artifacts removed!$(COLOR_RESET)"

clean-logs: ## 🗑️  Remove log files
	@echo "$(COLOR_BLUE)🗑️  Removing log files...$(COLOR_RESET)"
	@rm -rf $(LOGS_DIR)/*.log
	@echo "$(COLOR_GREEN)✅ Logs cleaned!$(COLOR_RESET)"

clean-all: clean ## 🗑️  Remove everything including venv
	@echo "$(COLOR_RED)⚠️  Removing virtual environment...$(COLOR_RESET)"
	@rm -rf $(VENV)
	@echo "$(COLOR_GREEN)✅ Complete cleanup done!$(COLOR_RESET)"

# ============================================================================
# DOCKER OPERATIONS
# ============================================================================

docker-build: ## 🐳 Build Docker image
	@echo "$(COLOR_BLUE)🐳 Building Docker image...$(COLOR_RESET)"
	@docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "$(COLOR_GREEN)✅ Docker image built: $(DOCKER_IMAGE):$(DOCKER_TAG)$(COLOR_RESET)"

docker-run: ## 🐳 Run Docker container
	@echo "$(COLOR_BLUE)🐳 Running Docker container...$(COLOR_RESET)"
	@docker run -d \
		--name $(PROJECT_NAME) \
		-p $(PORT):$(PORT) \
		--env-file $(ENV_FILE) \
		$(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo "$(COLOR_GREEN)✅ Container running on http://localhost:$(PORT)$(COLOR_RESET)"

docker-stop: ## 🐳 Stop Docker container
	@echo "$(COLOR_BLUE)🐳 Stopping Docker container...$(COLOR_RESET)"
	@docker stop $(PROJECT_NAME) || true
	@docker rm $(PROJECT_NAME) || true
	@echo "$(COLOR_GREEN)✅ Container stopped!$(COLOR_RESET)"

docker-logs: ## 🐳 Show Docker container logs
	@docker logs -f $(PROJECT_NAME)

docker-shell: ## 🐳 Open shell in Docker container
	@docker exec -it $(PROJECT_NAME) /bin/bash

docker-push: docker-build ## 🐳 Push Docker image to registry
	@echo "$(COLOR_BLUE)🐳 Pushing Docker image to registry...$(COLOR_RESET)"
	@docker tag $(DOCKER_IMAGE):$(DOCKER_TAG) $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)
	@docker push $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo "$(COLOR_GREEN)✅ Image pushed to registry!$(COLOR_RESET)"

docker-compose-up: ## 🐳 Start all services with docker-compose
	@echo "$(COLOR_BLUE)🐳 Starting services with docker-compose...$(COLOR_RESET)"
	@$(DOCKER_COMPOSE) up -d
	@echo "$(COLOR_GREEN)✅ Services started!$(COLOR_RESET)"

docker-compose-down: ## 🐳 Stop all services with docker-compose
	@echo "$(COLOR_BLUE)🐳 Stopping services...$(COLOR_RESET)"
	@$(DOCKER_COMPOSE) down
	@echo "$(COLOR_GREEN)✅ Services stopped!$(COLOR_RESET)"

docker-clean: ## 🐳 Remove all Docker artifacts
	@echo "$(COLOR_YELLOW)⚠️  Cleaning Docker artifacts...$(COLOR_RESET)"
	@docker system prune -af --volumes
	@echo "$(COLOR_GREEN)✅ Docker cleaned!$(COLOR_RESET)"

# ============================================================================
# DEPLOYMENT
# ============================================================================

deploy-aws: ## ☁️  Deploy to AWS EC2
	@echo "$(COLOR_BLUE)☁️  Deploying to AWS EC2...$(COLOR_RESET)"
	@bash scripts/deploy-aws.sh
	@echo "$(COLOR_GREEN)✅ Deployed to AWS!$(COLOR_RESET)"

deploy-heroku: ## ☁️  Deploy to Heroku
	@echo "$(COLOR_BLUE)☁️  Deploying to Heroku...$(COLOR_RESET)"
	@git push heroku main
	@heroku logs --tail
	@echo "$(COLOR_GREEN)✅ Deployed to Heroku!$(COLOR_RESET)"

deploy-docker: docker-build docker-push ## ☁️  Build and push Docker image
	@echo "$(COLOR_GREEN)✅ Docker deployment complete!$(COLOR_RESET)"

# ============================================================================
# DATABASE & MIGRATIONS (if using database)
# ============================================================================

db-migrate: ## 🗄️  Run database migrations
	@echo "$(COLOR_BLUE)🗄️  Running migrations...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && alembic upgrade head
	@echo "$(COLOR_GREEN)✅ Migrations complete!$(COLOR_RESET)"

db-rollback: ## 🗄️  Rollback last migration
	@echo "$(COLOR_YELLOW)⚠️  Rolling back migration...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && alembic downgrade -1
	@echo "$(COLOR_GREEN)✅ Rollback complete!$(COLOR_RESET)"

db-reset: ## 🗄️  Reset database (WARNING: deletes all data)
	@echo "$(COLOR_RED)⚠️  WARNING: This will delete all data!$(COLOR_RESET)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		. $(VENV)/bin/activate && alembic downgrade base; \
		. $(VENV)/bin/activate && alembic upgrade head; \
		echo "$(COLOR_GREEN)✅ Database reset!$(COLOR_RESET)"; \
	fi

# ============================================================================
# BACKUP & RESTORE
# ============================================================================

backup: ## 💾 Backup logs and data to AWS S3
	@echo "$(COLOR_BLUE)💾 Backing up to AWS S3...$(COLOR_RESET)"
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	aws s3 sync $(LOGS_DIR)/ s3://$(AWS_BUCKET)/backups/$$TIMESTAMP/logs/ \
		--region $(AWS_REGION) \
		--profile $(AWS_PROFILE)
	@echo "$(COLOR_GREEN)✅ Backup complete!$(COLOR_RESET)"

restore: ## 💾 Restore latest backup from AWS S3
	@echo "$(COLOR_BLUE)💾 Restoring from AWS S3...$(COLOR_RESET)"
	@aws s3 sync s3://$(AWS_BUCKET)/backups/latest/ ./data/backups/ \
		--region $(AWS_REGION) \
		--profile $(AWS_PROFILE)
	@echo "$(COLOR_GREEN)✅ Restore complete!$(COLOR_RESET)"

backup-local: ## 💾 Create local backup
	@echo "$(COLOR_BLUE)💾 Creating local backup...$(COLOR_RESET)"
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	tar -czf data/backups/backup_$$TIMESTAMP.tar.gz $(LOGS_DIR) $(ENV_FILE)
	@echo "$(COLOR_GREEN)✅ Local backup created!$(COLOR_RESET)"

# ============================================================================
# LOGS & MONITORING
# ============================================================================

logs: ## 📋 Show application logs (tail -f)
	@echo "$(COLOR_BLUE)📋 Showing application logs...$(COLOR_RESET)"
	@tail -f $(LOGS_DIR)/app.log

logs-error: ## 📋 Show error logs only
	@echo "$(COLOR_RED)📋 Showing error logs...$(COLOR_RESET)"
	@tail -f $(LOGS_DIR)/error.log

logs-clear: clean-logs ## 📋 Clear all logs

# ============================================================================
# DOCUMENTATION
# ============================================================================

docs: ## 📚 Generate documentation
	@echo "$(COLOR_BLUE)📚 Generating documentation...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && pdoc --html --output-dir $(DOCS_DIR) $(SRC_DIR)
	@echo "$(COLOR_GREEN)✅ Documentation generated in $(DOCS_DIR)$(COLOR_RESET)"

docs-serve: ## 📚 Serve documentation locally
	@echo "$(COLOR_BLUE)📚 Serving documentation on http://localhost:8080$(COLOR_RESET)"
	@. $(VENV)/bin/activate && pdoc --http localhost:8080 $(SRC_DIR)

# ============================================================================
# NGROK & WEBHOOK TESTING
# ============================================================================

ngrok: ## 🌐 Start ngrok tunnel
	@echo "$(COLOR_BLUE)🌐 Starting ngrok tunnel on port $(PORT)...$(COLOR_RESET)"
	@ngrok http $(PORT)

webhook-test: ## 🔗 Test webhook endpoint
	@echo "$(COLOR_BLUE)🔗 Testing webhook endpoint...$(COLOR_RESET)"
	@curl -X POST http://localhost:$(PORT)/webhook/gallabox \
		-H "Content-Type: application/json" \
		-d '{"test": "message", "from": "971501234567", "body": "Test message"}'
	@echo ""
	@echo "$(COLOR_GREEN)✅ Webhook test complete!$(COLOR_RESET)"

health-check: ## ❤️  Check application health
	@echo "$(COLOR_BLUE)❤️  Checking application health...$(COLOR_RESET)"
	@curl http://localhost:$(PORT)/health
	@echo ""

# ============================================================================
# SECURITY & AUDITING
# ============================================================================

security: ## 🔒 Run security checks
	@echo "$(COLOR_BLUE)🔒 Running security checks...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && bandit -r $(SRC_DIR) -ll
	@. $(VENV)/bin/activate && safety check
	@echo "$(COLOR_GREEN)✅ Security check complete!$(COLOR_RESET)"

audit: ## 🔍 Full security audit
	@echo "$(COLOR_BLUE)🔍 Running full security audit...$(COLOR_RESET)"
	@make security
	@make check-deps
	@echo "$(COLOR_GREEN)✅ Audit complete!$(COLOR_RESET)"

secrets-scan: ## 🔐 Scan for exposed secrets
	@echo "$(COLOR_BLUE)🔐 Scanning for secrets...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && detect-secrets scan --all-files --force-use-all-plugins
	@echo "$(COLOR_GREEN)✅ Secrets scan complete!$(COLOR_RESET)"

# ============================================================================
# UTILITIES
# ============================================================================

shell: ## 🐚 Open Python shell with project context
	@echo "$(COLOR_BLUE)🐚 Opening Python shell...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && $(PYTHON)

ipython: ## 🐚 Open IPython shell
	@echo "$(COLOR_BLUE)🐚 Opening IPython shell...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && ipython

version: ## 📌 Show version information
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)WhatsApp AI Support Agent v2.0.0$(COLOR_RESET)"
	@echo "Python version: $$($(PYTHON) --version)"
	@echo "Pip version: $$($(PIP) --version)"
	@echo "Project: $(PROJECT_NAME)"

env-check: ## ✅ Verify environment variables
	@echo "$(COLOR_BLUE)✅ Checking environment variables...$(COLOR_RESET)"
	@if [ -f $(ENV_FILE) ]; then \
		echo "$(COLOR_GREEN)✅ .env file exists$(COLOR_RESET)"; \
		. $(VENV)/bin/activate && python scripts/check_env.py; \
	else \
		echo "$(COLOR_RED)❌ .env file missing! Run 'make env-setup'$(COLOR_RESET)"; \
		exit 1; \
	fi

status: ## 📊 Show project status
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)Project Status:$(COLOR_RESET)"
	@echo "  Virtual Environment: $$(if [ -d $(VENV) ]; then echo '✅ Active'; else echo '❌ Not found'; fi)"
	@echo "  .env File: $$(if [ -f $(ENV_FILE) ]; then echo '✅ Present'; else echo '❌ Missing'; fi)"
	@echo "  Docker: $$(if command -v docker >/dev/null 2>&1; then echo '✅ Installed'; else echo '❌ Not installed'; fi)"
	@echo "  Ngrok: $$(if command -v ngrok >/dev/null 2>&1; then echo '✅ Installed'; else echo '❌ Not installed'; fi)"
	@echo "  Running Processes:"
	@ps aux | grep -E "uvicorn|ngrok|docker" | grep -v grep || echo "    No processes running"

init: setup ## 🎯 Initialize new project (alias for setup)

update: upgrade ## 🔄 Update all dependencies (alias for upgrade)

# ============================================================================
# CI/CD TARGETS
# ============================================================================

ci: install-dev lint test ## 🔄 Run CI pipeline (install, lint, test)
	@echo "$(COLOR_GREEN)✅ CI pipeline complete!$(COLOR_RESET)"

pre-commit: format lint test ## ✅ Pre-commit checks
	@echo "$(COLOR_GREEN)✅ Pre-commit checks passed!$(COLOR_RESET)"

# ============================================================================
# ALL-IN-ONE COMMANDS
# ============================================================================

all: clean install test lint ## 🎯 Run everything (clean, install, test, lint)
	@echo "$(COLOR_GREEN)✅ All tasks complete!$(COLOR_RESET)"

quickstart: setup run ## 🚀 Quick start (setup + run)

# ============================================================================
# CUSTOM SCRIPTS
# ============================================================================

create-ticket: ## 🎫 Create test Jira ticket via API
	@echo "$(COLOR_BLUE)🎫 Creating test Jira ticket...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && python scripts/create_test_ticket.py

simulate-conversation: ## 💬 Simulate WhatsApp conversation
	@echo "$(COLOR_BLUE)💬 Simulating conversation...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && python scripts/simulate_conversation.py

generate-report: ## 📊 Generate usage report
	@echo "$(COLOR_BLUE)📊 Generating usage report...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && python scripts/generate_report.py
	@echo "$(COLOR_GREEN)✅ Report saved to data/exports/$(COLOR_RESET)"

# ============================================================================
# PERFORMANCE & BENCHMARKING
# ============================================================================

benchmark: ## ⚡ Run performance benchmarks
	@echo "$(COLOR_BLUE)⚡ Running benchmarks...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && pytest tests/performance/ -v --benchmark-only
	@echo "$(COLOR_GREEN)✅ Benchmarks complete!$(COLOR_RESET)"

load-test: ## 🔥 Run load testing
	@echo "$(COLOR_BLUE)🔥 Running load tests...$(COLOR_RESET)"
	@. $(VENV)/bin/activate && locust -f tests/load/locustfile.py
	@echo "$(COLOR_GREEN)✅ Load test complete!$(COLOR_RESET)"

# ============================================================================
# SPECIAL TARGETS
# ============================================================================

.SILENT: help
.ONESHELL: deploy-aws deploy-heroku
.EXPORT_ALL_VARIABLES:

# ============================================================================
# END OF MAKEFILE
# ============================================================================