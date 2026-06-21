# NextUp — developer Makefile
# Targets delegate to docker compose, uv (backend), and npm (frontend).

COMPOSE := docker compose
API_DIR := apps/api
WEB_DIR := apps/web
.DEFAULT_GOAL := help

.PHONY: help setup up down restart logs build validate migrate makemigration \
        seed test test-api test-web lint lint-api lint-web format format-api \
        format-web typecheck clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup: ## Bootstrap local env: copy .env, generate mkcert TLS certs
	@bash scripts/setup.sh

up: ## Start the stack in the background
	$(COMPOSE) up -d

down: ## Stop the stack
	$(COMPOSE) down

restart: ## Restart the stack
	$(COMPOSE) down && $(COMPOSE) up -d

logs: ## Tail logs (use `make logs s=api` for one service)
	$(COMPOSE) logs -f $(s)

build: ## Build application images (api, web)
	$(COMPOSE) build api web

validate: ## Validate the docker-compose file
	$(COMPOSE) config --quiet && echo "compose OK"

migrate: ## Apply Alembic migrations (stack must be up)
	$(COMPOSE) run --rm api alembic upgrade head

makemigration: ## Autogenerate a migration: make makemigration m="message"
	$(COMPOSE) run --rm api alembic revision --autogenerate -m "$(m)"

seed: ## Load development seed data (admin/organizer/3 players, gym, runs)
	$(COMPOSE) run --rm api python -m app.seed

test: test-api test-web ## Run all test suites

test-api: ## Run backend tests (pytest against a throwaway Postgres)
	@bash scripts/test-api.sh

test-web: ## Run frontend tests (vitest)
	cd $(WEB_DIR) && npm test

lint: lint-api lint-web ## Lint backend + frontend

lint-api: ## Ruff lint + format check (backend)
	cd $(API_DIR) && uv run ruff check . && uv run ruff format --check .

lint-web: ## ESLint + type-check (frontend)
	cd $(WEB_DIR) && npm run lint && npm run typecheck

typecheck: ## mypy (backend) + tsc (frontend)
	cd $(API_DIR) && uv run mypy app
	cd $(WEB_DIR) && npm run typecheck

format: format-api format-web ## Format backend + frontend

format-api: ## Ruff format + import fix (backend)
	cd $(API_DIR) && uv run ruff format . && uv run ruff check --fix .

format-web: ## ESLint --fix (frontend)
	cd $(WEB_DIR) && npm run lint -- --fix

clean: ## Stop stack and remove volumes (DESTRUCTIVE — local data lost)
	$(COMPOSE) down -v
