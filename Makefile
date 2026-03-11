.PHONY: help install install-dev install-full install-ml install-solana clean test run-api run-demo setup env venv freeze help

# Colors for output
CYAN = \033[0;36m
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
NC = \033[0m # No Color

help:
	@echo "$(CYAN)Nova Memory 2.0 - Makefile Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup & Installation:$(NC)"
	@echo "  make setup           - Complete setup (creates venv, installs deps)"
	@echo "  make install         - Install core dependencies"
	@echo "  make install-dev     - Install with development tools"
	@echo "  make install-full    - Install all features (ML, Blockchain, Dev)"
	@echo "  make install-ml      - Install ML/AI dependencies"
	@echo "  make install-solana  - Install Solana blockchain support"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make test            - Run test suite"
	@echo "  make test-cov        - Run tests with coverage report"
	@echo "  make lint            - Run linters (flake8, black check)"
	@echo "  make format          - Format code with black"
	@echo "  make type-check      - Check types with mypy"
	@echo ""
	@echo "$(GREEN)Running:$(NC)"
	@echo "  make run-api         - Start REST API server"
	@echo "  make run-demo        - Run demo scenarios"
	@echo "  make run-main        - Run main tests"
	@echo ""
	@echo "$(GREEN)Maintenance:$(NC)"
	@echo "  make venv            - Create virtual environment"
	@echo "  make env             - Create .env from .env.example"
	@echo "  make freeze          - Generate pip freeze requirements"
	@echo "  make clean           - Remove generated files & cache"
	@echo "  make clean-all       - Clean + remove venv & database"
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make setup           # Quick start"
	@echo "  make install-full    # Full installation"
	@echo "  make run-api         # Start server"
	@echo "  make test            # Run tests"

# Setup targets
setup: venv env install test
	@echo "$(GREEN)✓ Setup complete!$(NC)"

venv:
	@echo "$(CYAN)Creating virtual environment...$(NC)"
	python3 -m venv venv
	@echo "$(GREEN)✓ Virtual environment created$(NC)"
	@echo "$(YELLOW)Activate with: source venv/bin/activate$(NC)"

env:
	@if [ ! -f .env ]; then \
		if [ -f .env.example ]; then \
			cp .env.example .env; \
			echo "$(GREEN)✓ Created .env from .env.example$(NC)"; \
			echo "$(YELLOW)⚠ Remember to update .env with your configuration!$(NC)"; \
		fi \
	else \
		echo "$(YELLOW)⚠ .env already exists$(NC)"; \
	fi

# Installation targets
install:
	@echo "$(CYAN)Installing core dependencies...$(NC)"
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-dev: install
	@echo "$(CYAN)Installing development dependencies...$(NC)"
	pip install -r requirements-dev.txt
	@echo "$(GREEN)✓ Development tools installed$(NC)"

install-full:
	@echo "$(CYAN)Installing all features...$(NC)"
	pip install --upgrade pip
	pip install -e ".[all,dev]"
	@echo "$(GREEN)✓ Full installation complete$(NC)"

install-ml:
	@echo "$(CYAN)Installing ML/AI dependencies...$(NC)"
	pip install -e ".[ml]"
	@echo "$(GREEN)✓ ML dependencies installed$(NC)"

install-solana:
	@echo "$(CYAN)Installing Solana blockchain support...$(NC)"
	pip install -e ".[blockchain]"
	@echo "$(GREEN)✓ Solana support installed$(NC)"

# Testing targets
test:
	@echo "$(CYAN)Running tests...$(NC)"
	python main.py

test-cov:
	@echo "$(CYAN)Running tests with coverage...$(NC)"
	pytest --cov=. --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(NC)"

# Code quality targets
lint:
	@echo "$(CYAN)Running linters...$(NC)"
	black --check .
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@echo "$(GREEN)✓ Linting complete$(NC)"

format:
	@echo "$(CYAN)Formatting code with black...$(NC)"
	black .
	@echo "$(GREEN)✓ Code formatted$(NC)"

type-check:
	@echo "$(CYAN)Checking types with mypy...$(NC)"
	mypy . --ignore-missing-imports
	@echo "$(GREEN)✓ Type checking complete$(NC)"

# Run targets
run-api:
	@echo "$(CYAN)Starting Nova Memory API Server...$(NC)"
	@echo "$(YELLOW)Swagger UI: http://localhost:8000/docs$(NC)"
	python -m api.server

run-demo:
	@echo "$(CYAN)Running demo scenarios...$(NC)"
	python demo_scenarios.py

run-main:
	@echo "$(CYAN)Running main tests...$(NC)"
	python main.py

# Maintenance targets
freeze:
	@echo "$(CYAN)Generating requirements...$(NC)"
	pip freeze > requirements-frozen.txt
	@echo "$(GREEN)✓ Frozen requirements saved to requirements-frozen.txt$(NC)"

clean:
	@echo "$(CYAN)Cleaning up...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -delete
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-all: clean
	@echo "$(YELLOW)Removing virtual environment and databases...$(NC)"
	rm -rf venv .venv
	rm -f nova_memory.db nova_memory.db-shm nova_memory.db-wal
	@echo "$(GREEN)✓ Full cleanup complete$(NC)"

# Development helpers
dev: install-dev
	@echo "$(GREEN)Development environment ready!$(NC)"
	@echo "$(CYAN)Useful commands:$(NC)"
	@echo "  make test      - Run tests"
	@echo "  make format    - Format code"
	@echo "  make lint      - Check code quality"
	@echo "  make run-api   - Start API server"

install-editable:
	@echo "$(CYAN)Installing in editable mode...$(NC)"
	pip install -e .
	@echo "$(GREEN)✓ Package installed in editable mode$(NC)"

.DEFAULT_GOAL := help
