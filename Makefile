.PHONY: help install dev-install test lint format clean docker-build docker-run deploy-local

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e .

dev-install: ## Install development dependencies
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e ".[dev]"

test: ## Run tests with coverage
	pytest tests/ -v --cov=src/devsecops_agent --cov-report=term --cov-report=html

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

lint: ## Run linters
	ruff check src/ tests/
	black --check src/ tests/
	mypy src/ --ignore-missing-imports

format: ## Format code
	black src/ tests/
	ruff check --fix src/ tests/

security-scan: ## Run security scans
	bandit -r src/ -f json -o bandit-report.json
	trivy fs --severity HIGH,CRITICAL .

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build: ## Build Docker image
	docker build -t devsecops-agent:latest .

docker-run: ## Run Docker container locally
	docker run -d \
		--name devsecops-agent \
		-p 8080:8080 \
		--env-file .env \
		-v $$(pwd)/data/chroma:/app/.devsecops/chroma \
		devsecops-agent:latest

docker-stop: ## Stop Docker container
	docker stop devsecops-agent
	docker rm devsecops-agent

docker-logs: ## View Docker logs
	docker logs -f devsecops-agent

compose-up: ## Start with docker-compose
	docker-compose up -d

compose-down: ## Stop docker-compose
	docker-compose down

compose-logs: ## View docker-compose logs
	docker-compose logs -f

compose-monitoring: ## Start with monitoring stack
	docker-compose --profile monitoring up -d

ingest-policies: ## Index policy documents
	python -m devsecops_agent --ingest examples/policies --reset

review-diff: ## Review a diff file (usage: make review-diff DIFF=path/to/diff)
	python -m devsecops_agent --diff $(DIFF) --rag

webhook-start: ## Start webhook server
	devsecops-webhook

health-check: ## Check service health
	curl http://localhost:8080/health

metrics: ## View metrics
	curl http://localhost:8080/metrics

setup-dev: dev-install ## Setup development environment
	cp .env.example .env
	@echo "Please edit .env with your API keys"

ci: lint test security-scan ## Run CI checks locally

deploy-staging: ## Deploy to staging (customize as needed)
	@echo "Deploying to staging..."
	# Add your staging deployment commands

deploy-prod: ## Deploy to production (customize as needed)
	@echo "Deploying to production..."
	# Add your production deployment commands

backup-chroma: ## Backup Chroma index
	tar -czf chroma-backup-$$(date +%Y%m%d-%H%M%S).tar.gz data/chroma/

restore-chroma: ## Restore Chroma index (usage: make restore-chroma BACKUP=file.tar.gz)
	tar -xzf $(BACKUP) -C data/
