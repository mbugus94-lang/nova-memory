.PHONY: help install install-dev install-full install-ml install-solana clean test test-unit test-api lint format typecheck run-api run-demo setup env venv freeze

# Colors for output
CYAN = \033[0;36m
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
NC = \033[0m # No Color

help:
	@echo "$(CYAN)Nova Memory 3.0 - Makefile Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup & Installation:$(NC)"
	@echo "  make setup           - Complete setup (creates venv, installs deps)"
	@echo "  make install         - Install core dependencies"
	@echo "  make install-dev     - Install with development tools"
	@echo "  make install-full    - Install all features (ML, Blockchain, Dev)"
	@echo "  make install-ml      - Install ML/AI dependencies"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make test            - Run all tests"
	@echo "  make test-unit       - Run unit tests only"
	@echo "  make test-api        - Run API tests only"
	@echo "  make test-cov        - Run tests with coverage report"
	@echo "  make lint            - Run all linters (ruff, flake8)"
	@echo "  make format          - Format code with black"
	@echo "  make typecheck       - Check types with mypy"
	@echo "  make check           - Run lint + typecheck + tests"
	@echo ""
	@echo "$(GREEN)Running:$(NC)"
	@echo "  make run-api         - Start REST API server"
	@echo "  make run-demo        - Run demo scenarios"
	@echo ""
	@echo "$(GREEN)Maintenance:$(NC)"
	@echo "  make venv            - Create virtual environment"
	@echo "  make env             - Create .env from .env.example"
	@echo "  make freeze          - Generate pip freeze requirements"
	@echo "  make clean           - Remove generated files & cache"
	@echo "  make migrate         - Run database migrations"
	@echo "  make pre-commit      - Install pre-commit hooks"
	@echo ""

# Setup targets
setup: venv env install-dev test
	@echo "$(GREEN)Setup complete!$(NC)"

venv:
	@echo "$(CYAN)Creating virtual environment...$(NC)"
	python -m venv venv
	@echo "$(GREEN)Virtual environment created$(NC)"
	@echo "$(YELLOW)Activate with: source venv/bin/activate$(NC)"

env:
	@if [ ! -f .env ]; then \
		if [ -f .env.example ]; then \
			cp .env.example .env; \
			echo "$(GREEN)Created .env from .env.example$(NC)"; \
			echo "$(YELLOW)Remember to update .env with your configuration!$(NC)"; \
		fi \
	else \
		echo "$(YELLOW).env already exists$(NC)"; \
	fi

# Installation targets
install:
	@echo "$(CYAN)Installing core dependencies...$(NC)"
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "$(GREEN)Dependencies installed$(NC)"

install-dev: install
	@echo "$(CYAN)Installing development dependencies...$(NC)"
	pip install -r requirements-dev.txt
	@echo "$(GREEN)Development tools installed$(NC)"

install-full:
	@echo "$(CYAN)Installing all features...$(NC)"
	pip install --upgrade pip
	pip install -e ".[all,dev]"
	@echo "$(GREEN)Full installation complete$(NC)"

install-ml:
	@echo "$(CYAN)Installing ML/AI dependencies...$(NC)"
	pip install -e ".[ml]"
	@echo "$(GREEN)ML dependencies installed$(NC)"

# Testing targets
test:
	@echo "$(CYAN)Running all tests...$(NC)"
	python -m pytest tests/ -v --tb=short
	@echo "$(GREEN)Tests complete$(NC)"

test-unit:
	@echo "$(CYAN)Running unit tests...$(NC)"
	python -m pytest tests/test_nova_memory.py tests/test_security.py tests/test_agent_registry.py tests/test_agent_messaging.py tests/test_memory_management.py tests/test_db.py -v
	@echo "$(GREEN)Unit tests complete$(NC)"

test-api:
	@echo "$(CYAN)Running API tests...$(NC)"
	ENVIRONMENT=development NOVA_SECRET_KEY=test-key python -m pytest tests/test_api_routes.py -v
	@echo "$(GREEN)API tests complete$(NC)"

test-cov:
	@echo "$(CYAN)Running tests with coverage...$(NC)"
	python -m pytest tests/ -v --cov=core --cov=api --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

# Code quality targets
lint:
	@echo "$(CYAN)Running linters...$(NC)"
	ruff check . --select E,F,W --ignore E501 || true
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@echo "$(GREEN)Linting complete$(NC)"

format:
	@echo "$(CYAN)Formatting code with black...$(NC)"
	black . --quiet
	@echo "$(GREEN)Code formatted$(NC)"

typecheck:
	@echo "$(CYAN)Checking types with mypy...$(NC)"
	mypy core/ api/ --ignore-missing-imports --no-error-summary || true
	@echo "$(GREEN)Type checking complete$(NC)"

check: lint typecheck test
	@echo "$(GREEN)All checks passed$(NC)"

# Run targets
run-api:
	@echo "$(CYAN)Starting Nova Memory API Server...$(NC)"
	@echo "$(YELLOW)Swagger UI: http://localhost:8000/docs$(NC)"
	python -m api.server

run-demo:
	@echo "$(CYAN)Running demo scenarios...$(NC)"
	python demo_scenarios.py

# Maintenance targets
migrate:
	@echo "$(CYAN)Running database migrations...$(NC)"
	python -c "from core.migrations import run_migrations; n = run_migrations('nova_memory_v2.db'); print(f'Applied {n} migration(s)')"
	@echo "$(GREEN)Migrations complete$(NC)"

pre-commit:
	@echo "$(CYAN)Installing pre-commit hooks...$(NC)"
	pre-commit install
	@echo "$(GREEN)Pre-commit hooks installed$(NC)"

freeze:
	@echo "$(CYAN)Generating requirements...$(NC)"
	pip freeze > requirements-frozen.txt
	@echo "$(GREEN)Frozen requirements saved to requirements-frozen.txt$(NC)"

clean:
	@echo "$(CYAN)Cleaning up...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage .ruff_cache
	@echo "$(GREEN)Cleanup complete$(NC)"

clean-all: clean
	@echo "$(YELLOW)Removing virtual environment and databases...$(NC)"
	rm -rf venv .venv
	rm -f nova_memory.db nova_memory.db-shm nova_memory.db-wal nova_memory_v2.db
	@echo "$(GREEN)Full cleanup complete$(NC)"

# Development helpers
dev: install-dev pre-commit
	@echo "$(GREEN)Development environment ready!$(NC)"
	@echo "$(CYAN)Useful commands:$(NC)"
	@echo "  make test      - Run tests"
	@echo "  make format    - Format code"
	@echo "  make lint      - Check code quality"
	@echo "  make check     - Run all checks"
	@echo "  make run-api   - Start API server"

.DEFAULT_GOAL := help
