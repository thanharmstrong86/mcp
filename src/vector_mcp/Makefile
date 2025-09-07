# Vector MCP Makefile

.PHONY: help install dev test lint format clean build run docker-build docker-run docker-stop

help: ## Show this help message
	@echo "Vector MCP Server - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync

dev: ## Install development dependencies
	uv sync --extra dev

test: ## Run tests
	uv run pytest tests/ -v

lint: ## Run linting
	uv run flake8 src/ tests/
	uv run mypy src/

format: ## Format code
	uv run black src/ tests/
	uv run isort src/ tests/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: ## Build the package
	uv build

run: ## Run the server locally
	uv run python start_server.py

run-dev: ## Run the server in development mode
	uv run python start_server.py --log-level DEBUG

docker-build: ## Build Docker image
	docker build -t vector-mcp:latest .

docker-run: ## Run with Docker Compose
	docker-compose up -d

docker-run-nginx: ## Run with Docker Compose including nginx
	docker-compose --profile nginx up -d

docker-stop: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-clean: ## Clean Docker resources
	docker-compose down -v
	docker rmi vector-mcp:latest || true

check-env: ## Check environment variables
	@echo "Checking required environment variables..."
	@python -c "import os; print('✅ SUPABASE_URL:', '✅' if os.getenv('SUPABASE_URL') else '❌ Missing')"
	@python -c "import os; print('✅ SUPABASE_ANON_KEY:', '✅' if os.getenv('SUPABASE_ANON_KEY') else '❌ Missing')"
	@python -c "import os; print('✅ OPENAI_API_KEY:', '✅' if os.getenv('OPENAI_API_KEY') else '❌ Missing')"

health: ## Check server health
	curl -f http://localhost:8002/health || echo "Server not responding"

setup: ## Initial setup
	cp .env.example .env
	@echo "Please edit .env file with your configuration"
	@echo "Then run: make install && make run"