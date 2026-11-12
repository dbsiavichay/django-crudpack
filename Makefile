.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[A-Za-z0-9_.-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Create the virtualenv and install dev dependencies
	uv sync

lint: ## Check code style and lint rules
	uv run ruff check .
	uv run ruff format --check .

format: ## Format code and apply safe lint fixes
	uv run ruff check --fix .
	uv run ruff format .

test: ## Run the test suite with coverage
	uv run pytest --cov --cov-report=term-missing

build: ## Build sdist and wheel into dist/
	rm -rf dist
	uv build
	uvx twine check --strict dist/*

.PHONY: help install lint format test build
